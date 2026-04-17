document.getElementById('triageForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // UI Elements
    const submitBtn = document.getElementById('predictBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    const resultContainer = document.getElementById('resultContainer');

    // Show loading state
    btnText.style.display = 'none';
    spinner.style.display = 'block';
    submitBtn.style.opacity = '0.8';
    submitBtn.style.cursor = 'not-allowed';

    // Collect data
    const formData = {
        age: parseFloat(document.getElementById('age').value),
        weight: parseFloat(document.getElementById('weight').value),
        sex: document.getElementById('sex').value,
        priority: document.getElementById('priority').value,
        reactions: document.getElementById('reactions').value
    };

    try {
        console.log("Sending prediction request...");
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Server error' }));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Prediction received:", data);

        if (data.status === 'success') {
            displayResults(data.risk_percentage);
        } else {
            throw new Error(data.message || 'Unknown error occurred');
        }

    } catch (error) {
        console.error('Prediction failed:', error);
        alert('Prediction Error: ' + error.message);
        resetBtnState();
    }
});

function resetBtnState() {
    const submitBtn = document.getElementById('predictBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    
    btnText.style.display = 'block';
    spinner.style.display = 'none';
    submitBtn.style.opacity = '1';
    submitBtn.style.cursor = 'pointer';
}

function displayResults(percentage) {
    // DO NOT hide form anymore - user wants both visible
    // document.querySelector('.form-container').style.display = 'none'; 
    
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.style.display = 'flex';
    
    // Tiny delay to allow display flex to apply before adding opacity class for animation
    setTimeout(() => {
        resultContainer.classList.add('show');
        // Smooth scroll to results
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);

    animateProgress(percentage);
    setRiskText(percentage);
    resetBtnState(); // Re-enable button so they can tweak inputs
}

function animateProgress(targetPercentage) {
    const riskValue = document.getElementById('riskValue');
    const circularProgress = document.getElementById('circularProgress');
    
    let currentVal = 0;
    const duration = 1500; // ms
    const interval = 20; // ms
    const step = targetPercentage / (duration / interval);
    
    let color = '#10B981'; // default green
    if (targetPercentage >= 40 && targetPercentage < 75) {
        color = '#F59E0B'; // warning orange
    } else if (targetPercentage >= 75) {
        color = '#EF4444'; // danger red
    }

    const timer = setInterval(() => {
        currentVal += step;
        if (currentVal >= targetPercentage) {
            currentVal = targetPercentage;
            clearInterval(timer);
        }
        
        riskValue.textContent = Math.round(currentVal) + '%';
        circularProgress.style.background = `conic-gradient(${color} ${currentVal * 3.6}deg, rgba(30, 41, 59, 0.7) 0deg)`;
        
        // Dynamic text coloring
        riskValue.style.color = color;
        
    }, interval);
}

function setRiskText(percentage) {
    const riskLevel = document.getElementById('riskLevel');
    const desc = document.getElementById('riskDescription');

    if (percentage < 40) {
        riskLevel.textContent = 'Low Risk';
        riskLevel.style.color = '#10B981';
        desc.textContent = 'The patient profile indicates a low probability of a serious adverse outcome.';
    } else if (percentage < 75) {
        riskLevel.textContent = 'Moderate Risk';
        riskLevel.style.color = '#F59E0B';
        desc.textContent = 'The patient profile shows moderate clinical risk. Monitor closely.';
    } else {
        riskLevel.textContent = 'High/Serious Risk';
        riskLevel.style.color = '#EF4444';
        desc.textContent = 'CRITICAL: The patient profile exhibits patterns highly correlated with severe adverse outcomes. Immediate intervention recommended.';
    }
}

function resetForm() {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.classList.remove('show');
    
    // Smooth scroll back to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    setTimeout(() => {
        resultContainer.style.display = 'none';
        // document.querySelector('.form-container').style.display = 'block'; // Always visible now
        document.getElementById('triageForm').reset();
        resetBtnState();
        
        // Reset circular progress
        const circularProgress = document.getElementById('circularProgress');
        circularProgress.style.background = `conic-gradient(var(--bg-dark) 0deg, var(--card-bg) 0deg)`;
        document.getElementById('riskValue').style.color = '#fff';
        document.getElementById('riskValue').textContent = '0%';
        
    }, 400); // match CSS transition time
}
