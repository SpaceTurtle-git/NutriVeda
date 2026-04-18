/* ── DIET OPTION SELECTION ── */
document.querySelectorAll('.diet-option').forEach(label => {
  label.addEventListener('click', () => {
    const name = label.querySelector('input').name;
    document.querySelectorAll(`.diet-option`).forEach(l => {
      if (l.querySelector('input').name === name) l.classList.remove('selected');
    });
    label.classList.add('selected');
    label.querySelector('input').checked = true;
  });
});

/* ── DOSHA OPTION SELECTION ── */
document.querySelectorAll('.dosha-option').forEach(label => {
  label.addEventListener('click', () => {
    const qid = label.dataset.qid;
    document.querySelectorAll(`[data-qid="${qid}"]`).forEach(l => l.classList.remove('selected'));
    label.classList.add('selected');
    label.querySelector('input').checked = true;
  });
});

/* ── INTAKE FORM SUBMISSION ── */
const intakeForm = document.getElementById('intake-form');
if (intakeForm) {
  intakeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btnText   = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const btn       = document.getElementById('submit-btn');

    // Collect answers
    const answers = {};
    document.querySelectorAll('.dosha-option.selected').forEach(el => {
      answers[el.dataset.qid] = el.dataset.value;
    });

    const dietPref = document.querySelector('input[name="dietary_preference"]:checked')?.value;

    // Validate
    if (!document.getElementById('name').value.trim()) {
      showToast('Please enter your name.', 'error'); return;
    }
    if (!document.getElementById('age').value) {
      showToast('Please enter your age.', 'error'); return;
    }
    if (!document.getElementById('weight').value) {
      showToast('Please enter your weight.', 'error'); return;
    }
    if (!dietPref) {
      showToast('Please select a dietary preference.', 'error'); return;
    }
    if (Object.keys(answers).length < 3) {
      showToast('Please answer all 3 dosha questions.', 'error'); return;
    }

    // Loading state
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    btn.disabled = true;

    const payload = {
      name: document.getElementById('name').value.trim(),
      age: parseInt(document.getElementById('age').value),
      weight: parseFloat(document.getElementById('weight').value),
      dietary_preference: dietPref,
      answers,
    };

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        showToast(data.error || 'Something went wrong.', 'error');
        return;
      }

      showToast('Plan generated! Redirecting…', 'success');
      setTimeout(() => { window.location.href = data.redirect; }, 800);

    } catch (err) {
      showToast('Network error. Please try again.', 'error');
      console.error(err);
    } finally {
      btnText.classList.remove('hidden');
      btnLoader.classList.add('hidden');
      btn.disabled = false;
    }
  });
}

/* ── DASHBOARD: MEAL PLAN RENDERING ── */
if (typeof PLAN_DATA !== 'undefined' && PLAN_DATA) {
  const days = PLAN_DATA.plan_data.days;
  let activeDay = 0;

  // Day abbreviations
  const dayAbbr = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

  // Build tabs
  const tabContainer = document.getElementById('day-tabs');
  if (tabContainer) {
    days.forEach((day, i) => {
      const tab = document.createElement('button');
      tab.className = `day-tab ${i === 0 ? 'active' : ''}`;
      tab.textContent = dayAbbr[i] || `D${i+1}`;
      tab.addEventListener('click', () => selectDay(i));
      tabContainer.appendChild(tab);
    });
  }

  function selectDay(index) {
    activeDay = index;
    // Update tabs
    document.querySelectorAll('.day-tab').forEach((t, i) => {
      t.classList.toggle('active', i === index);
    });
    renderMeals(days[index]);

    // Update daily tip
    const tipEl = document.getElementById('daily-tip');
    if (tipEl) tipEl.textContent = days[index].daily_tip || '';
  }

  function renderMeals(day) {
    const container = document.getElementById('meal-display');
    if (!container) return;

    const mealColors = {
      breakfast: '#E8935A20',
      lunch:     '#7BAE7F20',
      dinner:    '#5A9BE820',
    };
    const mealEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙' };

    container.innerHTML = '';
    ['breakfast', 'lunch', 'dinner'].forEach(mealType => {
      const meal = day[mealType];
      if (!meal) return;

      const card = document.createElement('div');
      card.className = 'meal-card';

      const ingredientHTML = (meal.ingredients || [])
        .map(ing => `<span class="ingredient-tag">${ing}</span>`)
        .join('');

      card.innerHTML = `
        <div class="meal-card-header" style="background:${mealColors[mealType]}">
          ${mealEmoji[mealType]} ${mealType.toUpperCase()}
        </div>
        <div class="meal-card-body space-y-3">
          <h4 class="font-display font-700 text-base leading-tight">${meal.name}</h4>
          <p class="text-xs text-bark/60 leading-relaxed">${meal.description}</p>
          <div>${ingredientHTML}</div>
          <div class="border-t-2 border-bark/10 pt-3">
            <p class="text-xs font-600 text-sage uppercase tracking-wider mb-1">Benefits</p>
            <p class="text-xs text-bark/70 italic">${meal.benefits}</p>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // Render first day on load
  selectDay(0);
}

/* ── DASHBOARD: UPDATE FORM ── */
const updateForm = document.getElementById('update-form');
if (updateForm && typeof USER_DATA !== 'undefined') {
  // Sync diet option selection on update form
  document.querySelectorAll('#update-modal .diet-option').forEach(label => {
    label.addEventListener('click', () => {
      document.querySelectorAll('#update-modal .diet-option').forEach(l => l.classList.remove('selected'));
      label.classList.add('selected');
      label.querySelector('input').checked = true;
    });
  });

  updateForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btnText   = document.getElementById('update-btn-text');
    const btnLoader = document.getElementById('update-btn-loader');
    const btn       = document.getElementById('update-btn');

    const dietPref = document.querySelector('input[name="u_diet"]:checked')?.value;

    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    btn.disabled = true;

    const payload = {
      name: document.getElementById('u-name').value.trim(),
      age: parseInt(document.getElementById('u-age').value),
      weight: parseFloat(document.getElementById('u-weight').value),
      dietary_preference: dietPref,
    };

    try {
      const res = await fetch(`/api/profile/${USER_DATA.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) {
        showToast(data.error || 'Update failed.', 'error');
        return;
      }

      showToast('Profile updated & plan regenerated!', 'success');
      setTimeout(() => window.location.reload(), 1000);

    } catch (err) {
      showToast('Network error.', 'error');
    } finally {
      btnText.classList.remove('hidden');
      btnLoader.classList.add('hidden');
      btn.disabled = false;
    }
  });
}
