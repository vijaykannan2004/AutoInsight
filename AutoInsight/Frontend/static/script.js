// ===== AutoInsight Dashboard - Script =====

// 🌗 Toggle Dark Mode
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("themeToggle");
  toggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    toggleBtn.textContent = document.body.classList.contains("dark-mode")
      ? "☀️ Light Mode"
      : "🌙 Dark Mode";
  });

  // 📤 File Upload Handling
  const uploadForm = document.getElementById("uploadForm");
  const fileInput = document.getElementById("csvFile");
  const resultDiv = document.getElementById("result");

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a CSV file first.");
      return;
    }

    resultDiv.innerHTML = `<p class="loading">⏳ Analyzing your data...</p>`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      console.log("Backend Response:", data);  // 🔍 Debug

      if (data.status === "success") {

        // FIX: Detect if AI returned an error
        let aiInsightText = "";
        if (typeof data.ai_insights === "string") {
          if (data.ai_insights.includes("API key expired")) {
            aiInsightText = "❌ AI key was expired earlier — Please re-upload your file.";
          } else {
            aiInsightText = data.ai_insights;
          }
        } else {
          aiInsightText = "⚠️ AI did not return insights.";
        }

        resultDiv.innerHTML = `
          <h2>📊 Dataset Summary</h2>
          <p><strong>Rows:</strong> ${data.cleaning_report.rows}</p>
          <p><strong>Columns:</strong> ${data.cleaning_report.cols}</p>

          <h3>🧠 AI Insights (Updated)</h3>
          <p>${aiInsightText}</p>

          <h3>📈 Highly Correlated Columns</h3>
          <pre>${JSON.stringify(data.cleaning_report.highly_correlated_pairs, null, 2)}</pre>
        `;
      } else {
        resultDiv.innerHTML = `<p style="color:red;">Error: ${data.detail}</p>`;
      }
    } catch (error) {
      resultDiv.innerHTML = `<p style="color:red;">❌ Failed to connect to API</p>`;
      console.error(error);
    }
  });
});
