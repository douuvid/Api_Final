<template>
  <div class="register-container">
    <h2>Inscription</h2>
    <form @submit.prevent="handleRegister">
      <div class="form-group">
        <label for="first_name">Prénom:</label>
        <input type="text" id="first_name" v-model="form.first_name" required>
      </div>
      <div class="form-group">
        <label for="last_name">Nom:</label>
        <input type="text" id="last_name" v-model="form.last_name" required>
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="form.email" required>
      </div>
      <div class="form-group">
        <label for="password">Mot de passe:</label>
        <input type="password" id="password" v-model="form.password" required>
      </div>

      <div class="form-group">
        <label for="phone">Numéro de téléphone:</label>
        <input type="tel" id="phone" v-model="form.phone" placeholder="Ex: 0612345678" required>
      </div>

      <hr>
      <p>Vos préférences de recherche :</p>

      <div class="form-group">
        <label for="search_query">Poste recherché:</label>
        <input type="text" id="search_query" v-model="form.search_query" placeholder="Ex: Développeur Python">
      </div>

      <div class="form-group">
        <label for="contract_type">Type de contrat:</label>
        <select id="contract_type" v-model="form.contract_type">
          <option value="">Indifférent</option>
          <option value="CDI">CDI</option>
          <option value="CDD">CDD</option>
          <option value="Stage">Stage</option>
          <option value="Alternance">Alternance</option>
        </select>
      </div>

      <div class="form-group">
        <label for="location">Localisation:</label>
        <select id="location" v-model="form.location">
          <option value="Toute la France">Toute la France</option>
          <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
        </select>
      </div>

      <button type="submit">S'inscrire</button>
    </form>
    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      form: {
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone: '',
        search_query: '',
        contract_type: '',
        location: 'Toute la France'
      },
      regions: [
        "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", 
        "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France", 
        "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie", 
        "Pays de la Loire", "Provence-Alpes-Côte d'Azur"
      ],
      message: ''
    };
  },
  methods: {
    async handleRegister() {
      this.message = '';
      try {
        const response = await axios.post('http://localhost:8000/register', this.form);
        this.message = response.data.message || 'Inscription réussie!';
        setTimeout(() => {
          this.$router.push('/login');
        }, 2000);
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
          this.message = `Erreur: ${error.response.data.detail}`;
        } else {
          this.message = 'Une erreur est survenue lors de l\'inscription.';
        }
      }
    }
  }
};
</script>

<style scoped>
.register-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
h2 {
  text-align: center;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
}
label {
  display: block;
  margin-bottom: 0.5rem;
}
input {
  width: 100%;
  padding: 0.75rem;
  box-sizing: border-box;
  border: 1px solid #ccc;
  border-radius: 4px;
}
button {
  width: 100%;
  padding: 0.75rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
button:hover {
  background-color: #369f73;
}
.message {
  margin-top: 1rem;
  text-align: center;
}
</style>
