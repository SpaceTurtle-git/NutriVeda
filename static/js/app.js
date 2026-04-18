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
      showToast('Please answer all 9 dosha questions.', 'error'); return;
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

    // Check if recipe data is available
    const hasRecipe = meal.has_recipe === true;
    const recipeBtn = hasRecipe ? 
      `<button onclick="showRecipeModal('${mealType}', ${day.day})" class="brutal-btn bg-sage text-cream text-xs px-3 py-1 mt-3">📖 View Full Recipe</button>` : 
      `<div class="text-xs text-bark/50 italic mt-3"> ⏳ Generating Recipe Details</div>`;

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
        ${recipeBtn}
      </div>
    `;
    container.appendChild(card);
  });
}

// Store the current plan data globally for recipe lookup
let currentPlanData = PLAN_DATA;

// Function to show recipe modal
function showRecipeModal(mealType, dayNumber) {
  if (!currentPlanData || !currentPlanData.plan_data) {
    showToast('Recipe data not available', 'error');
    return;
  }
  
  const day = currentPlanData.plan_data.days.find(d => d.day === dayNumber);
  if (!day) return;
  
  const meal = day[mealType];
  if (!meal || !meal.recipe) {
    showToast('Recipe details not found', 'error');
    return;
  }
  
  const recipe = meal.recipe;
  const title = document.getElementById('recipe-title');
  const content = document.getElementById('recipe-content');
  
  // Extract ingredients and measures (up to 20)
  let ingredientsList = '';
  for (let i = 1; i <= 20; i++) {
    const ingredient = recipe[`strIngredient${i}`];
    const measure = recipe[`strMeasure${i}`];
    if (ingredient && ingredient.trim()) {
      ingredientsList += `<li class="flex items-start gap-2 text-sm"><span class="font-600">${measure || ''}</span> ${ingredient}</li>`;
    }
  }
  
  title.textContent = recipe.strMeal;
  
  content.innerHTML = `
    <div class="space-y-4">
      <div class="flex justify-center">
        <img src="${recipe.strMealThumb}" alt="${recipe.strMeal}" class="w-full max-h-64 object-cover rounded-none border-2 border-bark" />
      </div>
      <div class="grid grid-cols-2 gap-2 text-sm">
        <p><strong class="font-600">Category:</strong> ${recipe.strCategory || 'N/A'}</p>
        <p><strong class="font-600">Cuisine:</strong> ${recipe.strArea || 'N/A'}</p>
      </div>
      <div>
        <h4 class="font-display font-700 text-lg mb-2">Ingredients</h4>
        <ul class="grid grid-cols-1 md:grid-cols-2 gap-1 text-sm">${ingredientsList}</ul>
      </div>
      <div>
        <h4 class="font-display font-700 text-lg mb-2">Instructions</h4>
        <p class="text-sm whitespace-pre-wrap">${recipe.strInstructions || 'No instructions available.'}</p>
      </div>
      ${recipe.strYoutube ? `<div><h4 class="font-display font-700 text-lg mb-2">Video Tutorial</h4><a href="${recipe.strYoutube}" target="_blank" class="brutal-btn bg-sage text-cream text-sm px-4 py-2 inline-block">Watch on YouTube</a></div>` : ''}
    </div>
  `;
  
  document.getElementById('recipe-modal').classList.remove('hidden');
}

// Function to close recipe modal
function closeRecipeModal() {
  document.getElementById('recipe-modal').classList.add('hidden');
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
