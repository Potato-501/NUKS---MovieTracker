// --- COMPONENTS ---
const SearchPage = {
    template: '#search-template',
    data() {
        return { query: '', results: [] }
    },
    methods: {
        async search() {
            const res = await fetch(`http://127.0.0.1:5000/movies/search?q=${this.query}`);
            const data = await res.json();
            this.results = data.Search || [];
        },
        async add(movie, status) {
            const res = await fetch('http://127.0.0.1:5000/movies/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: movie.Title, year: movie.Year, status })
            });
            const data = await res.json();
            if (res.ok) {
                alert(`Saved to ${status}!`);
            } else {
                alert(`Error: ${data.error}`);
            }
        }
    }
}

const ListPage = {
    template: '#list-template',
    props: ['type'], // Tells us if we are 'watchlist' or 'library'
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
        // metoda za nalaganje filmov v frontend iz database-a glede na status (watchlist ali library)
        async loadMovies() {
            console.log("Fetching movies for:", this.type);
            const res = await fetch('http://127.0.0.1:5000/movies/');
            const allMovies = await res.json();
            this.movies = allMovies.filter(m => m.status === this.type);
        },

        // metoda za premikanje filma iz watchlista v library
        async moveMovie(movie_id) {
            try {
                const res = await fetch(`http://127.0.0.1:5000/movies/${movie_id}/status`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'library' })
                });
                if (res.ok) await this.loadMovies();
            }
            catch (e) {
                alert("Error moving movie: " + e.message);
            }
        },

        // metoda za brisanje filma iz baze
        async deleteMovie(movie_id) {
            if (!confirm("Are you sure you want to delete this movie?")) return;

            try {
                const res = await fetch(`http://127.0.0.1:5000/movies/${movie_id}`, { method: 'DELETE' });
                if (res.ok) await this.loadMovies();
            }
            catch (e) {
                alert("Error deleting movie: " + e.message);
            }
        },

        // metoda za nastavljanje ocene filma v library-ju
        async setRating(movie_id, rating) {
            try {
                const res = await fetch(`http://127.0.0.1:5000/movies/${movie_id}/rating`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rating })
                });
                if (res.ok) {
                    const movie = this.movies.find(m => m.id === movie_id);
                    movie.rating = rating; // Update local state for instant UI feedback
                }
            }
            catch (e) {
                alert("Error setting rating: " + e.message);
            }
        }
    }
}

// --- ROUTER ---
const routes = [
    { path: '/', component: SearchPage },
    { path: '/watchlist', component: ListPage, props: { type: 'watchlist' } },
    { path: '/library', component: ListPage, props: { type: 'library' } }
];

const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes
});

// --- INIT ---
const app = Vue.createApp({});
app.use(router);
app.mount('#app');