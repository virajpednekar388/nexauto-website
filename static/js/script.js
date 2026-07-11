// Global Application UI Actions and Event Interception Handling
document.addEventListener('submit', function(e) {
    if (e.target && e.target.id === 'admissionForm') {
        e.preventDefault();
        
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        
        // Show status transition indicator states
        submitBtn.innerHTML = 'Processing Application... <i class="fa-solid fa-spinner fa-spin"></i>';
        submitBtn.disabled = true;

        // Bundle form payloads strictly into standard structured JSON notation mapping
        const formData = new FormData(form);
        const jsonPayload = Object.fromEntries(formData.entries());

        // Relative path targeting our monolithic Flask endpoint securely
        fetch('/api/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonPayload)
        })
        .then(response => {
            if (!response.ok) throw new Error("Server communication fault");
            return response.json();
        })
        .then(result => {
            alert("Success! Your admission details are now secured inside our Neon Relational Cloud Database.");
            form.reset();
        })
        .catch(error => {
            console.error('Database Connectivity Error:', error);
            alert("Submission error encountered. Please check server execution connections.");
        })
        .finally(() => {
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
        });
    }
});