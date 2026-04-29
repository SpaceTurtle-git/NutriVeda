// ──────────────────────────────────────────────
// PDF Download – Full 7‑Day Meal Plan
// ──────────────────────────────────────────────

document.getElementById('download-pdf-btn')?.addEventListener('click', function() {
  if (!PLAN_DATA || !PLAN_DATA.plan_data || !PLAN_DATA.plan_data.days) {
    showToast('No meal plan data available.', 'error');
    return;
  }

  const days = PLAN_DATA.plan_data.days;
  const user = USER_DATA;
  const doshaInfo = DOSHA_INFO;

  // Create a temporary div with the PDF content
  const pdfContent = document.createElement('div');
  pdfContent.className = 'pdf-content';
  pdfContent.style.padding = '40px 30px';
  pdfContent.style.fontFamily = "'DM Sans', sans-serif";
  pdfContent.style.backgroundColor = '#F5F0E8';
  pdfContent.style.color = '#2C2416';
  pdfContent.style.border = '2px solid #2C2416';

  // Header
  pdfContent.innerHTML = `
    <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #2C2416; padding-bottom: 20px;">
      <h1 style="font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; margin: 0;">Nutriveda</h1>
      <p style="font-size: 14px; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px;">Personalized 7‑Day Meal Plan</p>
    </div>

    <div style="display: flex; justify-content: space-between; margin-bottom: 30px; gap: 20px;">
      <div style="border: 2px solid #2C2416; padding: 15px; flex: 1; background: white;">
        <h3 style="font-family: 'Syne'; font-size: 18px; margin: 0 0 10px 0;">Your Profile</h3>
        <p><strong>Name:</strong> ${user.name}</p>
        <p><strong>Age:</strong> ${user.age} yrs</p>
        <p><strong>Weight:</strong> ${user.weight} kg</p>
        <p><strong>Diet:</strong> ${user.dietary_preference === 'veg' ? 'Vegetarian 🥦' : 'Non-Veg 🍗'}</p>
      </div>
      <div style="border: 2px solid #2C2416; padding: 15px; flex: 1; background: white;">
        <h3 style="font-family: 'Syne'; font-size: 18px; margin: 0 0 10px 0;">Your Dosha: ${user.primary_dosha}</h3>
        <p><strong>Element:</strong> ${doshaInfo.element}</p>
        <p><strong>Traits:</strong> ${doshaInfo.traits}</p>
        <p><strong>Dietary Focus:</strong> ${doshaInfo.dietary_focus}</p>
        <p><strong>Avoid:</strong> ${doshaInfo.avoid}</p>
      </div>
    </div>

    <h2 style="font-family: 'Syne'; font-size: 22px; border-left: 6px solid #7BAE7F; padding-left: 15px; margin: 20px 0;">Your 7‑Day Meal Plan</h2>
    <div id="pdf-days-container"></div>
    <div style="margin-top: 30px; text-align: center; font-size: 10px; color: #2C2416; border-top: 1px solid #2C2416; padding-top: 15px;">
      Generated on ${new Date().toLocaleDateString()} · Nutriveda — Eat right for your dosha.
    </div>
  `;

  // Build days HTML
  const daysContainer = pdfContent.querySelector('#pdf-days-container');
  const mealColors = {
    breakfast: '#E8935A20',
    lunch: '#7BAE7F20',
    dinner: '#5A9BE820',
  };
  const mealEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' };

  days.forEach(day => {
    const dayDiv = document.createElement('div');
    dayDiv.style.marginBottom = '35px';
    dayDiv.style.pageBreakInside = 'avoid';
    dayDiv.style.border = '2px solid #2C2416';
    dayDiv.style.background = 'white';
    dayDiv.style.boxShadow = '4px 4px 0 #2C2416';

    let mealsHtml = '';
    ['breakfast', 'lunch', 'dinner'].forEach(mealType => {
      const meal = day[mealType];
      if (!meal) return;
      const ingredientsHtml = (meal.ingredients || []).map(ing => 
        `<span style="display: inline-block; background: #F5F0E8; border: 1px solid #2C2416; padding: 2px 8px; margin: 2px; font-size: 10px;">${ing}</span>`
      ).join('');

      mealsHtml += `
        <div style="border-bottom: 1px solid #2C2416; padding: 12px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 20px;">${mealEmoji[mealType]}</span>
            <h4 style="font-family: 'Syne'; font-size: 16px; font-weight: 700; margin: 0; text-transform: uppercase;">${mealType}</h4>
          </div>
          <p style="font-weight: 700; margin: 5px 0;">${meal.name}</p>
          <p style="font-size: 12px; color: #2C2416;">${meal.description}</p>
          <div style="margin: 8px 0;">${ingredientsHtml}</div>
          <p style="font-size: 11px; font-style: italic;"><strong>Benefits:</strong> ${meal.benefits}</p>
        </div>
      `;
    });

    dayDiv.innerHTML = `
      <div style="background: #2C2416; color: white; padding: 8px 12px; font-family: 'Syne'; font-weight: 700; font-size: 18px;">
        Day ${day.day} · ${day.day_name || ''}
      </div>
      ${mealsHtml}
      <div style="background: #F5F0E8; padding: 8px 12px; border-top: 1px solid #2C2416; font-size: 12px;">
        <strong>Daily Tip:</strong> ${day.daily_tip || 'Stay mindful and hydrated.'}
      </div>
    `;
    daysContainer.appendChild(dayDiv);
  });

  // Options for html2pdf
  const opt = {
    margin:        [0.5, 0.5, 0.5, 0.5], // top, right, bottom, left (inches)
    filename:     `Nutriveda_${user.name.replace(/\s/g, '_')}_${new Date().toISOString().slice(0,10)}.pdf`,
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, letterRendering: true, useCORS: true },
    jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
  };

  // Generate PDF
  html2pdf().set(opt).from(pdfContent).save();
});