const API_BASE = (() => {
    const explicitBase = window.__MOVIEKITE_API_BASE__ || '';
    if (explicitBase) {
        return explicitBase.replace(/\/$/, '');
    }

    // If frontend is not served by Flask backend, default API calls to local Flask server.
    if (window.location.protocol === 'file:') {
        return 'http://127.0.0.1:5000';
    }

    return '';
})();

function apiUrl(path) {
    return `${API_BASE}${path}`;
}

async function sessionFetch(url, options = {}) {
    const response = await fetch(apiUrl(url), {
        credentials: 'include',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });

    if (response.status === 401) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Please log in first.');
    }

    return response;
}

async function fetchCurrentUser() {
    const res = await fetch(apiUrl('/api/auth/me'), { credentials: 'include' });
    const data = await res.json();
    return data.user || null;
}

async function fetchUserListStats() {
    try {
        const res = await sessionFetch('/movies/');
        const movies = await res.json();
        return movies.reduce((stats, movie) => {
            if (movie.status === 'watchlist') {
                stats.watchlist += 1;
            }
            if (movie.status === 'library') {
                stats.library += 1;
            }
            return stats;
        }, { watchlist: 0, library: 0 });
    }
    catch (e) {
        return { watchlist: 0, library: 0 };
    }
}

// --- COMPONENTS ---
const SearchPage = {
    template: '#search-template',
    data() {
        return { query: '', results: [] }
    },
    methods: {
        async search() {
            const res = await fetch(apiUrl(`/movies/search?q=${encodeURIComponent(this.query)}`));
            const data = await res.json();
            this.results = data.Search || [];
        },
        async add(movie, status) {
            if (!this.$root.currentUser) {
                alert('Please log in to save movies.');
                return;
            }

            const res = await sessionFetch('/movies/add', {
                method: 'POST',
                body: JSON.stringify({
                    title: movie.Title,
                    year: movie.Year,
                    status,
                    poster_url: movie.Poster
                })
            });
            const data = await res.json();
            if (res.ok) {
                alert(`Saved to ${status}!`);
                this.$root.listStats = await fetchUserListStats();
            } else {
                alert(`Error: ${data.error}`);
            }
        }
    }
}

const ProfilePage = {
    template: '#profile-template',
    computed: {
        currentUser() {
            return this.$root.currentUser;
        }
    },
    methods: {
        logout() {
            this.$root.logout();
        }
    }
};

const ListPage = {
    template: '#list-template',
    props: ['type'],
    data() { return { movies: [] } },
    watch: {
        type: {
            handler: 'loadMovies',
            immediate: true
        }
    },
    computed: {
        title() { return this.type === 'watchlist' ? 'My Watchlist' : 'My Library'; }
    },
    methods: {
        normalizePosterUrl(url) {
            if (!url) return '';
            if (url.startsWith('http://') || url.startsWith('https://')) {
                return `/movies/poster?url=${encodeURIComponent(url)}`;
            }
            return url;
        },

        async loadMovies() {
            try {
                const res = await sessionFetch('/movies/');
                const allMovies = await res.json();
                this.movies = allMovies
                    .filter(m => m.status === this.type)
                    .map(m => ({ ...m, poster_url: this.normalizePosterUrl(m.poster_url) }));

                if (this.type === 'library') {
                    this.movies.forEach(movie => {
                        this.loadNotes(movie);
                    });
                }
            }
            catch (e) {
                this.movies = [];
                console.warn(e.message);
            }
        },

        async moveMovie(movie_id) {
            try {
                const res = await sessionFetch(`/movies/${movie_id}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: 'library' })
                });
                if (res.ok) {
                    await this.loadMovies();
                    this.$root.listStats = await fetchUserListStats();
                }
            }
            catch (e) {
                alert('Error moving movie: ' + e.message);
            }
        },

        async deleteMovie(movie_id) {
            if (!confirm('Are you sure you want to delete this movie?')) return;

            try {
                const res = await sessionFetch(`/movies/${movie_id}`, { method: 'DELETE' });
                if (res.ok) {
                    await this.loadMovies();
                    this.$root.listStats = await fetchUserListStats();
                }
            }
            catch (e) {
                alert('Error deleting movie: ' + e.message);
            }
        },

        async setRating(movie_id, rating) {
            try {
                const res = await sessionFetch(`/movies/${movie_id}/rating`, {
                    method: 'PATCH',
                    body: JSON.stringify({ rating })
                });
                if (res.ok) {
                    const movie = this.movies.find(m => m.id === movie_id);
                    movie.rating = rating;
                }
            }
            catch (e) {
                alert('Error setting rating: ' + e.message);
            }
        },

        async loadNotes(movie) {
            try {
                const res = await sessionFetch(`/api/reviews/${movie.id}`);
                const data = await res.json();
                movie.note = data.note;
            }
            catch (e) {
                alert('Error loading note: ' + e.message);
            }
        },

        async saveNote(movie) {
            try {
                const res = await sessionFetch(`/api/reviews/${movie.id}`, {
                    method: 'POST',
                    body: JSON.stringify({ note: movie.note })
                });
                if (res.ok) {
                    return;
                } else {
                    let text;
                    try { text = await res.text(); } catch (err) { text = String(err); }
                    alert('Error saving note: ' + (text || res.status));
                }
            }
            catch (e) {
                alert('Error saving note: ' + e.message);
            }
        }
    }
};

// --- ROUTER ---
const routes = [
    { path: '/', component: SearchPage },
    { path: '/watchlist', component: ListPage, props: { type: 'watchlist' }, meta: { requiresAuth: true } },
    { path: '/library', component: ListPage, props: { type: 'library' }, meta: { requiresAuth: true } },
    { path: '/profile', component: ProfilePage, meta: { requiresAuth: true } }
];

const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes
});

router.beforeEach(async (to) => {
    if (!to.meta.requiresAuth) {
        return true;
    }

    const user = await fetchCurrentUser();
    if (!user) {
        return '/';
    }

    return true;
});

// --- INIT ---
const app = Vue.createApp({
    data() {
        return {
            currentUser: null,
            listStats: { watchlist: 0, library: 0 },
            showAuthModal: false,
            authMode: 'login',
            authForm: {
                identifier: '',
                username: '',
                email: '',
                password: '',
                confirmPassword: ''
            },
            authError: ''
        };
    },
    async mounted() {
        await this.loadSession();
    },
    methods: {
        async loadSession() {
            this.currentUser = await fetchCurrentUser();
            if (this.currentUser) {
                this.listStats = await fetchUserListStats();
            } else {
                this.listStats = { watchlist: 0, library: 0 };
            }
        },
        openAuth(mode) {
            this.authMode = mode;
            this.authError = '';
            this.authForm = {
                identifier: '',
                username: '',
                email: '',
                password: '',
                confirmPassword: ''
            };
            this.showAuthModal = true;
        },
        closeAuth() {
            this.showAuthModal = false;
            this.authError = '';
        },
        async submitAuth() {
            try {
                if (this.authMode === 'signup' && this.authForm.password !== this.authForm.confirmPassword) {
                    this.authError = 'Passwords do not match.';
                    return;
                }

                const endpoint = this.authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
                const payload = this.authMode === 'login'
                    ? {
                        identifier: this.authForm.identifier,
                        password: this.authForm.password
                    }
                    : {
                        username: this.authForm.username,
                        email: this.authForm.email,
                        password: this.authForm.password
                    };

                const res = await fetch(apiUrl(endpoint), {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();

                if (!res.ok) {
                    this.authError = data.error || 'Authentication failed.';
                    return;
                }

                this.currentUser = data.user;
                this.listStats = await fetchUserListStats();
                this.closeAuth();
                await this.loadSession();
            }
            catch (e) {
                this.authError = e.message;
            }
        },
        async logout() {
            await fetch(apiUrl('/api/auth/logout'), {
                method: 'POST',
                credentials: 'include'
            });
            this.currentUser = null;
            this.listStats = { watchlist: 0, library: 0 };
            router.push('/');
        }
    }
});
app.use(router);
app.mount('#app');
