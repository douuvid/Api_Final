<template>
  <div class="profile-container">
    <h2>Profil Utilisateur</h2>
    <div v-if="user" class="user-info">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <p><strong>Nom:</strong> {{ user.first_name }} {{ user.last_name }}</p>
      <p><strong>ID Utilisateur:</strong> {{ user.id }}</p>
    </div>
    <div v-else>
      <p>Chargement des informations...</p>
    </div>
    <button @click="logout">Se déconnecter</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      user: null
    };
  },
  async created() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.$router.push('/login');
      return;
    }
    try {
      const response = await axios.get('http://localhost:8080/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      this.user = response.data;
    } catch (error) {
      console.error('Erreur de récupération du profil:', error);
      localStorage.removeItem('access_token');
      this.$router.push('/login');
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('access_token');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 50px auto;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.user-info p {
  font-size: 1.1rem;
  line-height: 1.6;
}
button {
  margin-top: 20px;
  padding: 0.75rem 1.5rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
button:hover {
  background-color: #c82333;
}
</style>
