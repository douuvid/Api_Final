<template>
  <div class="home">
    <h1>Recherche d'Offres d'Emploi</h1>
    <div class="search-bar">
      <input v-model="keywords" type="text" placeholder="Mots-clés (ex: développeur)" />
      <input v-model="location" type="text" placeholder="Département (ex: 75)" />
      <button @click="searchJobs">Rechercher</button>
    </div>

    <div v-if="loading" class="loading">
      <p>Chargement...</p>
    </div>

    <div v-if="error" class="error">
      <p>Erreur: {{ error }}</p>
    </div>

    <div v-if="results && results.resultats && results.resultats.length" class="results">
      <h2>Résultats</h2>
      <job-offer-card
        v-for="offer in results.resultats"
        :key="offer.id"
        :offer="offer"
      />
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import JobOfferCard from '../components/JobOfferCard.vue';

export default {
  name: 'HomeView',
  components: {
    JobOfferCard,
  },
  data() {
    return {
      keywords: 'développeur',
      location: '75', // Utiliser le numéro du département
      results: null,
      loading: false,
      error: null,
    };
  },
  methods: {
    async searchJobs() {
      this.loading = true;
      this.error = null;
      this.results = null;

      try {
        // L'URL du backend Flask
        const apiUrl = 'http://127.0.0.1:5000/api/search';
        const response = await axios.get(apiUrl, {
          params: {
            motsCles: this.keywords,
            departement: this.location,
          },
        });
        this.results = response.data;
      } catch (err) {
        this.error = err.message || 'Une erreur est survenue lors de la recherche.';
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: sans-serif;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-bar input {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  flex-grow: 1;
}

.search-bar button {
  padding: 10px 20px;
  font-size: 16px;
  color: white;
  background-color: #007bff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-bar button:hover {
  background-color: #0056b3;
}

.loading, .error {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
}

.loading {
  background-color: #e3f2fd;
  color: #0d47a1;
}

.error {
  background-color: #ffebee;
  color: #c62828;
}

.results pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap; /* Pour que le texte aille à la ligne */
  word-wrap: break-word;
}
</style>
