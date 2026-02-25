document.addEventListener("DOMContentLoaded", function () {

    const valueInput = document.getElementById("voucherValue");
    const expiryInput = document.querySelector("input[name='expiry']");
    const previewBox = document.getElementById("previewBox");
    const previewValue = document.getElementById("previewValue");
    const previewPoints = document.getElementById("previewPoints");
    const previewTier = document.getElementById("previewTier");

    function calculatePreview() {

        const value = parseFloat(valueInput.value);
        const expiryDate = new Date(expiryInput.value);
        const today = new Date();

        if (!value || value <= 0 || !expiryInput.value) {
            previewBox.classList.add("hidden");
            return;
        }

        // Calculate days remaining
        const timeDiff = expiryDate - today;
        const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));

        let expiryMultiplier = 1;

        if (daysLeft > 90) expiryMultiplier = 1.0;
        else if (daysLeft > 30) expiryMultiplier = 0.85;
        else if (daysLeft > 7) expiryMultiplier = 0.65;
        else if (daysLeft > 0) expiryMultiplier = 0.40;
        else expiryMultiplier = 0; // expired

        const credits = Math.floor(value * 0.8 * expiryMultiplier);

        // Tier logic
        let tier = "Standard";
        if (value >= 3000) tier = "Premium";
        else if (value >= 1500) tier = "Gold";

        previewValue.innerText = "₹" + value;
        previewPoints.innerText = credits;
        previewTier.innerText = tier;

        previewBox.classList.remove("hidden");
    }

    valueInput.addEventListener("input", calculatePreview);
    expiryInput.addEventListener("change", calculatePreview);

});

// Trigger animation after form submit
const form = document.querySelector("form");
const modal = document.getElementById("successModal");

form.addEventListener("submit", function (e) {
    e.preventDefault(); // remove if using real backend redirect

    const credits = parseInt(document.getElementById("previewPoints").innerText) || 0;

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    const processing = document.getElementById("processingState");
    const completed = document.getElementById("completedState");

    // Fake processing delay
    setTimeout(() => {

        processing.classList.add("hidden");
        completed.classList.remove("hidden");

        // Animate checkmark
        const path = document.getElementById("checkPath");
        path.style.transition = "stroke-dashoffset 0.8s ease";
        path.style.strokeDashoffset = "0";

        // Generate transaction ID
        const txnId = "TXN-" + Math.random().toString(36).substr(2, 9).toUpperCase();
        document.getElementById("txnId").innerText = txnId;

        // Animate credits count up
        animateCredits(credits);

    }, 1800);
});


function animateCredits(finalValue) {
    let current = 0;
    const increment = Math.ceil(finalValue / 40);

    const counter = setInterval(() => {
        current += increment;
        if (current >= finalValue) {
            current = finalValue;
            clearInterval(counter);
        }
        document.getElementById("finalCredits").innerText = current;
    }, 30);
}

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const credits = parseInt(document.getElementById("previewPoints").innerText) || 0;

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    const processing = document.getElementById("processingState");
    const completed = document.getElementById("completedState");

    setTimeout(() => {

        processing.classList.add("hidden");
        completed.classList.remove("hidden");

        const path = document.getElementById("checkPath");
        path.style.transition = "stroke-dashoffset 0.8s ease";
        path.style.strokeDashoffset = "0";

        const txnId = "TXN-" + Math.random().toString(36).substr(2, 9).toUpperCase();
        document.getElementById("txnId").innerText = txnId;

        animateCredits(credits);

        // 🚀 AUTO REDIRECT AFTER 3.2 SECONDS
        setTimeout(() => {
            window.location.href = "/dashboard?success=1";
        }, 3200);

    }, 1500);
});