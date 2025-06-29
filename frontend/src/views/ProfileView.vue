<template>
  <div class="profile-container">
    <h2>Profil Utilisateur</h2>
    <div v-if="user" class="user-info">
      <p><strong>Email:</strong> {{ user.email }}</p>
      <p><strong>Nom:</strong> {{ user.first_name }} {{ user.last_name }}</p>
      <!-- Document Status -->
      <p><strong>CV:</strong> {{ user.cv_path ? getFilename(user.cv_path) : 'Aucun CV téléversé' }}</p>
      <p><strong>Lettre de motivation:</strong> {{ user.lm_path ? getFilename(user.lm_path) : 'Aucune lettre de motivation téléversée' }}</p>
    </div>
    <div v-else>
      <p>Chargement des informations...</p>
    </div>

    <hr class="separator">

    <!-- Upload Section -->
    <div class="upload-section">
      <h3>Mes documents</h3>
      
      <!-- CV Upload Form -->
      <form @submit.prevent="handleUpload('cv')" class="upload-form">
        <label for="cv-upload">Téléverser un nouveau CV</label>
        <input id="cv-upload" type="file" @change="onFileSelected($event, 'cv')" accept=".pdf,.doc,.docx">
        <button type="submit" :disabled="!selectedCvFile">Envoyer le CV</button>
      </form>

      <!-- LM Upload Form -->
      <form @submit.prevent="handleUpload('lm')" class="upload-form">
        <label for="lm-upload">Téléverser une nouvelle Lettre de Motivation</label>
        <input id="lm-upload" type="file" @change="onFileSelected($event, 'lm')" accept=".pdf,.doc,.docx">
        <button type="submit" :disabled="!selectedLmFile">Envoyer la Lettre de Motivation</button>
      </form>

      <!-- Feedback Messages -->
      <div v-if="uploadMessage" class="feedback-message success">{{ uploadMessage }}</div>
      <div v-if="uploadError" class="feedback-message error">{{ uploadError }}</div>
    </div>

    <hr class="separator">

    <button @click="logout" class="logout-button">Se déconnecter</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      user: null,
      selectedCvFile: null,
      selectedLmFile: null,
      uploadMessage: '',
      uploadError: ''
    };
  },
  async created() {
    await this.fetchUserProfile();
  },
  methods: {
    async fetchUserProfile() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        this.$router.push('/login');
        return;
      }
      try {
        const response = await axios.get('http://localhost:8080/users/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.user = response.data;
      } catch (error) {
        console.error('Erreur de récupération du profil:', error);
        this.logout(); // Logout if token is invalid or expired
      }
    },
    onFileSelected(event, docType) {
      const file = event.target.files[0];
      if (docType === 'cv') {
        this.selectedCvFile = file;
      } else if (docType === 'lm') {
        this.selectedLmFile = file;
      }
    },
    async handleUpload(docType) {
      this.uploadMessage = '';
      this.uploadError = '';

      const file = docType === 'cv' ? this.selectedCvFile : this.selectedLmFile;
      if (!file) {
        this.uploadError = 'Veuillez sélectionner un fichier.';
        return;
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);

      const token = localStorage.getItem('access_token');
      try {
        await axios.post('http://localhost:8080/users/me/upload-document', formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        this.uploadMessage = `Votre ${docType === 'cv' ? 'CV' : 'lettre de motivation'} a été téléversé(e) avec succès.`;
        // Reset file input and refresh user data
        if (docType === 'cv') this.selectedCvFile = null;
        else this.selectedLmFile = null;
        document.getElementById(`${docType}-upload`).value = null;
        
        await this.fetchUserProfile(); // Refresh user data to show new file path

      } catch (error) {
        console.error(`Erreur lors de l'upload du ${docType}:`, error);
        this.uploadError = `Échec de l'upload. ${error.response?.data?.detail || 'Veuillez réessayer.'}`;
      }
    },
    getFilename(path) {
        if (!path) return '';
        // Handles both Unix-like (/) and Windows (\) separators
        return path.split(/[\\/]/).pop();
    },
    logout() {
      localStorage.removeItem('access_token');
      this.user = null; // Clear user data on logout
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
  font-family: sans-serif;
}
.user-info p {
  font-size: 1.1rem;
  line-height: 1.6;
}
.separator {
  border: 0;
  border-top: 1px solid #eee;
  margin: 2rem 0;
}
.upload-section h3 {
  margin-bottom: 1.5rem;
}
.upload-form {
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.upload-form label {
  font-weight: bold;
}
.upload-form input[type="file"] {
  border: 1px solid #ccc;
  padding: 8px;
  border-radius: 4px;
}
.upload-form button {
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  align-self: flex-start;
}
.upload-form button:disabled {
  background-color: #a0a0a0;
  cursor: not-allowed;
}
.upload-form button:hover:not(:disabled) {
  background-color: #0056b3;
}
.feedback-message {
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
}
.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}
.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
.logout-button {
  padding: 0.75rem 1.5rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.logout-button:hover {
  background-color: #c82333;
}
</style>
