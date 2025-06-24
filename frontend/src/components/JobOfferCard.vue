<template>
  <div class="job-card">
    <h3>{{ offer.intitule }}</h3>
    <p class="company" v-if="offer.entreprise && offer.entreprise.nom">
      {{ offer.entreprise.nom }}
    </p>
    <p class="location" v-if="offer.lieuTravail">
      {{ offer.lieuTravail.libelle }}
    </p>
    <p class="contract-type" v-if="offer.typeContratLibelle">
      {{ offer.typeContratLibelle }}
    </p>
    <div class="description" v-if="offer.description">
      <p>{{ offer.description.substring(0, 150) }}...</p>
    </div>
    <a :href="offer.origineOffre.urlOrigine" target="_blank" class="details-button">Voir l'offre</a>
  </div>
</template>

<script>
export default {
  name: 'JobOfferCard',
  props: {
    offer: {
      type: Object,
      required: true,
    },
  },
};
</script>

<style scoped>
.job-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.3s ease;
}

.job-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

h3 {
  margin-top: 0;
  color: #333;
}

.company {
  font-weight: bold;
  color: #555;
}

.location, .contract-type {
  color: #777;
  font-size: 0.9em;
}

.description {
  margin-top: 10px;
  font-size: 0.95em;
  color: #444;
}

.details-button {
  display: inline-block;
  margin-top: 15px;
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: bold;
  transition: background-color 0.3s ease;
}

.details-button:hover {
  background-color: #0056b3;
}
</style>
