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
    <!-- SECTION MES CANDIDATURES IQUESTA -->
    <div class="candidatures-section" v-if="applications && applications.length">
      <h2>Mes candidatures</h2>
      <div class="candidature-card" v-for="(app, idx) in applications" :key="app.offer_url">
        <div class="candidature-header">
          <span class="dot"></span>
          <span class="job-title">{{ app.title }}</span> -
          <span class="company">{{ app.company }}</span>
          <span class="location">({{ app.location }})</span>
        </div>
        <div class="candidature-status">
          Statut : <span :class="statusClass(app.status)">{{ app.status }}</span> - {{ formatDate(app.applied_at) }}
        </div>
        <div class="candidature-actions">
          <button @click="showDetails(app)">Détails</button>
          <a :href="app.offer_url" target="_blank" rel="noopener noreferrer">Voir l'offre</a>
        </div>
      </div>
      <!-- Modal détails -->
      <div v-if="modalApp" class="modal-overlay" @click.self="modalApp = null">
        <div class="modal-content">
          <h3>{{ modalApp.title }} - {{ modalApp.company }}</h3>
          <p><strong>Lieu :</strong> {{ modalApp.location }}</p>
          <p><strong>Description :</strong></p>
          <pre>{{ modalApp.description }}</pre>
          <p><a :href="modalApp.offer_url" target="_blank">Voir l'offre</a></p>
          <button @click="modalApp = null">Fermer</button>
        </div>
      </div>
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
      // --- Pour les candidatures iQuesta ---
      applications: [],
      modalApp: null,
    };
  },
  methods: {
    async fetchApplications() {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        const response = await axios.get('http://localhost:8000/users/me/applications', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.applications = response.data;
      } catch (e) {
        this.applications = [];
      }
    },
    showDetails(app) {
      this.modalApp = app;
    },
    formatDate(dateStr) {
      if (!dateStr) return '';
      const d = new Date(dateStr);
      return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },
    statusClass(status) {
      switch ((status||'').toLowerCase()) {
        case 'candidature envoyée': return 'statut-envoye';
        case 'déjà postulé': return 'statut-deja';
        case 'échec candidature': return 'statut-echec';
        default: return 'statut-autre';
      }
    },
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
  mounted() {
    this.fetchApplications();
  },
};
</script>

<style scoped>
.candidatures-section {
  margin: 40px 0 0 0;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  padding: 24px;
  background: #fafbfc;
}
.candidature-card {
  border-bottom: 1px solid #e0e0e0;
  padding: 14px 0 12px 0;
  margin-bottom: 10px;
}
.candidature-header {
  font-size: 1.1em;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot {
  height: 10px;
  width: 10px;
  background-color: #007bff;
  border-radius: 50%;
  display: inline-block;
  margin-right: 7px;
}
.job-title { color: #222; }
.company { color: #007bff; font-weight: 500; }
.location { color: #888; }
.candidature-status {
  margin: 3px 0 0 22px;
  font-size: 0.95em;
}
.statut-envoye { color: #28a745; font-weight: bold; }
.statut-deja { color: #ff9800; font-weight: bold; }
.statut-echec { color: #c62828; font-weight: bold; }
.statut-autre { color: #555; font-weight: bold; }
.candidature-actions {
  margin-top: 5px;
  margin-left: 22px;
  display: flex;
  gap: 10px;
}
.candidature-actions button,
.candidature-actions a {
  background: #f5f5f5;
  border: 1px solid #bbb;
  border-radius: 4px;
  padding: 5px 13px;
  text-decoration: none;
  color: #222;
  cursor: pointer;
  font-size: 0.95em;
  transition: background 0.2s;
}
.candidature-actions button:hover,
.candidature-actions a:hover {
  background: #e0e0e0;
}
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: #fff;
  border-radius: 8px;
  padding: 28px 32px;
  min-width: 320px;
  max-width: 80vw;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
.modal-content h3 { margin-top: 0; }
.modal-content pre {
  background: #f9f9f9;
  border-radius: 4px;
  padding: 12px;
  font-size: 0.97em;
  max-height: 200px;
  overflow-y: auto;
}
.modal-content button {
  margin-top: 18px;
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 18px;
  cursor: pointer;
}
.modal-content button:hover {
  background: #0056b3;
}
</style>


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
