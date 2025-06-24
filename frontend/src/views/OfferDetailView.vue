<template>
  <div class="offer-detail-view">
    <div v-if="loading" class="loading">
      <p>Chargement des détails de l'offre...</p>
    </div>
    <div v-if="error" class="error">
      <p>Erreur: {{ error }}</p>
    </div>
    <div v-if="offer" class="offer-content">
      <h1>{{ offer.intitule }}</h1>
      <div class="offer-header">
        <p v-if="offer.entreprise && offer.entreprise.nom" class="company"><strong>Entreprise:</strong> {{ offer.entreprise.nom }}</p>
        <p v-if="offer.lieuTravail" class="location"><strong>Lieu:</strong> {{ offer.lieuTravail.libelle }}</p>
        <p v-if="offer.typeContratLibelle" class="contract"><strong>Contrat:</strong> {{ offer.typeContratLibelle }}</p>
        <p v-if="offer.salaire && offer.salaire.libelle" class="salary"><strong>Salaire:</strong> {{ offer.salaire.libelle }}</p>
      </div>
      <hr />
      <h2>Description de l'offre</h2>
      <div class="description" v-html="offer.description"></div>

      <div v-if="offer.competences && offer.competences.length">
        <h2>Compétences requises</h2>
        <ul class="skills">
          <li v-for="skill in offer.competences" :key="skill.libelle">{{ skill.libelle }}</li>
        </ul>
      </div>

      <a :href="offer.origineOffre.urlOrigine" target="_blank" class="apply-button">Postuler sur le site d'origine</a>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'OfferDetailView',
  props: ['id'],
  data() {
    return {
      offer: null,
      loading: false,
      error: null,
    };
  },
  async created() {
    this.loading = true;
    try {
      const apiUrl = `http://127.0.0.1:5000/api/job_details/${this.id}`;
      const response = await axios.get(apiUrl);
      this.offer = response.data;
    } catch (err) {
      this.error = err.response?.data?.error || err.message || 'Une erreur est survenue.';
      console.error(err);
    } finally {
      this.loading = false;
    }
  },
};
</script>

<style scoped>
.offer-detail-view {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
  font-family: sans-serif;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.offer-header p {
  margin: 5px 0;
}
.description {
  line-height: 1.6;
}
.skills {
  list-style-type: none;
  padding: 0;
}
.skills li {
  background-color: #e3f2fd;
  color: #0d47a1;
  padding: 5px 10px;
  border-radius: 15px;
  display: inline-block;
  margin: 5px;
}
.apply-button {
  display: inline-block;
  margin-top: 25px;
  padding: 12px 25px;
  background-color: #28a745;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  font-weight: bold;
  transition: background-color 0.3s ease;
}
.apply-button:hover {
  background-color: #218838;
}
</style>
