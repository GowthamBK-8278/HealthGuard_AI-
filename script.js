document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 HealthGuard Loaded");

    document.querySelectorAll(".card").forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.boxShadow = "0 0 40px cyan";
        });

        card.addEventListener("mouseleave", () => {
            card.style.boxShadow = "0 0 25px rgba(0,255,255,0.2)";
        });
    });
});