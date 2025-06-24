<template>
  <div class="home">
    <h1>Recherche d'Offres d'Emploi</h1>
    <div class="search-bar">
      <input v-model="keywords" type="text" placeholder="Mots-clés (ex: développeur)" />
      <input v-model="location" type="text" placeholder="Département (ex: 75)" />
      <button @click="searchJobs">Rechercher</button>
    </div>

    <hr class="separator" />

    <div class="scraper-section">
      <h2>Candidature Automatisée</h2>
      <p>Entrez vos identifiants France Travail pour lancer le processus sur les critères ci-dessus.</p>
      <div class="credentials">
        <input v-model="identifiant" type="text" placeholder="Votre identifiant France Travail" />
        <input v-model="mot_de_passe" type="password" placeholder="Votre mot de passe" />
      </div>
      <button @click="lancerScrapingAutomatique" :disabled="isScraping">
        {{ isScraping ? 'Candidatures en cours...' : 'Lancer les candidatures' }}
      </button>
      
      <div v-if="isScraping || scrapingLogs.length > 0" class="scraper-output">
        <h3>Progression</h3>

        <div v-if="totalOffers > 0" class="progress-container">
          <progress :value="currentProgress" :max="totalOffers"></progress>
          <span>{{ currentProgress }} / {{ totalOffers }} offres traitées</span>
        </div>

        <ul class="logs">
          <li v-for="(log, index) in scrapingLogs" :key="index">{{ log }}</li>
        </ul>
        <div v-if="isScraping && totalOffers === 0" class="loading">
          <p>Initialisation...</p>
        </div>
      </div>

      <div v-if="scrapingError" class="error">
        <p>Erreur du scraper: {{ scrapingError }}</p>
      </div>

      <div v-if="scrapingResult" class="results">
        <h3>Résumé Final</h3>
        <ul>
          <li>📊 Offres traitées au total : {{ scrapingResult.offres_traitees }}</li>
          <li>✅ Candidatures envoyées avec succès : {{ scrapingResult.candidatures_reussies }}</li>
          <li>📄 Offres avec candidature directe (réussies ou non) : {{ scrapingResult.offres_directes }}</li>
          <li>↪️  Offres avec redirection externe : {{ scrapingResult.redirections_externes }}</li>
          <li>👍 Offres déjà postulées (ignorées) : {{ scrapingResult.deja_postule }}</li>
        </ul>
      </div>
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
      // --- Pour le scraper ---
      identifiant: '',
      mot_de_passe: '',
      isScraping: false,
      scrapingResult: null,
      scrapingError: null,
      scrapingLogs: [],
      totalOffers: 0,
      currentProgress: 0,
    };
  },
  methods: {
    async lancerScrapingAutomatique() {
      if (!this.identifiant || !this.mot_de_passe || !this.keywords || !this.location) {
        this.scrapingError = 'Veuillez remplir les mots-clés, la localisation et vos identifiants.';
        return;
      }

      this.isScraping = true;
      this.scrapingError = null;
      this.scrapingResult = null;
      this.scrapingLogs = [];
      this.totalOffers = 0;
      this.currentProgress = 0;

      try {
        const response = await fetch('http://127.0.0.1:5000/api/lancer-scraping', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            identifiant: this.identifiant,
            mot_de_passe: this.mot_de_passe,
            mots_cles: this.keywords,
            localisation: this.location,
          }),
        });

        if (!response.ok) {
          throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n\n');
          
          lines.forEach(line => {
            if (line.startsWith('data: ')) {
              const data = line.substring(6);
              if (data.startsWith('TOTAL_OFFERS:')) {
                this.totalOffers = parseInt(data.substring(13), 10);
              } else if (data.startsWith('PROGRESS:')) {
                this.currentProgress = parseInt(data.substring(9), 10);
              } else if (data.startsWith('FIN:')) {
                const jsonResult = JSON.parse(data.substring(4));
                this.scrapingResult = jsonResult;
                this.isScraping = false;
              } else {
                this.scrapingLogs.push(data);
              }
            }
          });
        }

      } catch (err) {
        this.scrapingError = err.message || 'Une erreur est survenue lors de la connexion au scraper.';
        this.isScraping = false;
      } 
    },

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

.separator {
  border: none;
  border-top: 1px solid #eee;
  margin: 30px 0;
}

.scraper-section {
  margin-top: 20px;
}

.credentials {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.credentials input {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.scraper-section button {
  padding: 10px 20px;
  font-size: 16px;
  color: white;
  background-color: #28a745;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
}

.scraper-section button:hover {
  background-color: #218838;
}

.scraper-section button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.scraper-output {
  margin-top: 20px;
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 4px;
}

.progress-container {
  margin-bottom: 15px;
}

.progress-container progress {
  width: 100%;
  height: 25px;
}

.progress-container span {
  display: block;
  text-align: center;
  margin-top: 5px;
}

.logs {
  list-style-type: none;
  padding: 0;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 10px;
  margin-bottom: 10px;
}

.logs li {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
  font-family: monospace;
}

.results ul {
  list-style-type: none;
  padding: 0;
}

.results li {
  font-size: 16px;
  margin-bottom: 8px;
}

.results pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap; /* Pour que le texte aille à la ligne */
  word-wrap: break-word;
}
</style>
