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

    <hr class="separator">

    <!-- Section Préférences de Recherche -->
    <div class="preferences-section">
      <h3>Mes préférences de recherche</h3>
      <form @submit.prevent="handleUpdatePreferences" class="preferences-form">
        <div class="form-group">
          <label for="search_query">Poste recherché:</label>
          <input type="text" id="search_query" v-model="preferencesForm.search_query" placeholder="Ex: Développeur Python">
        </div>
        <div class="form-group">
          <label for="contract_type">Type de contrat:</label>
          <select id="contract_type" v-model="preferencesForm.contract_type">
            <option value="">Indifférent</option>
            <option value="CDI">CDI</option>
            <option value="CDD">CDD</option>
            <option value="Stage">Stage</option>
            <option value="Alternance">Alternance</option>
          </select>
        </div>
        <div class="form-group">
          <label for="location">Localisation:</label>
          <select id="location" v-model="preferencesForm.location">
            <option value="Toute la France">Toute la France</option>
            <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
          </select>
        </div>
        <button type="submit">Mettre à jour les préférences</button>
      </form>
      <div v-if="preferencesMessage" class="feedback-message success">{{ preferencesMessage }}</div>
      <div v-if="preferencesError" class="feedback-message error">{{ preferencesError }}</div>
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
      uploadError: '',
      preferencesForm: {
        search_query: '',
        contract_type: '',
        location: ''
      },
      regions: [
        "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", 
        "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France", 
        "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie", 
        "Pays de la Loire", "Provence-Alpes-Côte d'Azur"
      ],
      preferencesMessage: '',
      preferencesError: ''
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
        // Populate preferences form
        this.preferencesForm.search_query = this.user.search_query || '';
        this.preferencesForm.contract_type = this.user.contract_type || '';
        this.preferencesForm.location = this.user.location || 'Toute la France';
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
    async handleUpdatePreferences() {
      this.preferencesMessage = '';
      this.preferencesError = '';
      const token = localStorage.getItem('access_token');
      try {
        const response = await axios.put('http://localhost:8080/users/me/preferences', this.preferencesForm, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.preferencesMessage = response.data.message || 'Préférences mises à jour avec succès !';
        await this.fetchUserProfile(); // Refresh user data
      } catch (error) {
        console.error('Erreur lors de la mise à jour des préférences:', error);
        this.preferencesError = `Échec de la mise à jour. ${error.response?.data?.detail || 'Veuillez réessayer.'}`;
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
.preferences-section {
  margin-top: 2rem;
}
.preferences-form .form-group {
  margin-bottom: 1rem;
}
.preferences-form label {
  display: block;
  margin-bottom: 0.5rem;
}
.preferences-form input,
.preferences-form select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.preferences-form button {
  width: 100%;
  padding: 0.75rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.preferences-form button:hover {
  background-color: #0056b3;
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
