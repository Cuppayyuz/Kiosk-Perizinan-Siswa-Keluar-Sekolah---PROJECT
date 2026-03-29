/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",  // <-- PENTING: Scan semua file HTML di folder templates
    "./static/**/*.js"        // Scan file JS jika ada
  ],
  theme: {
    extend: {
      // Disini kamu bisa nambahin warna custom sekolahmu nanti
      colors: {
        'sekolah-primary': '#1e40af', 
        'sekolah-secondary': '#1e293b',
      }
    },
  },
  plugins: [],
}