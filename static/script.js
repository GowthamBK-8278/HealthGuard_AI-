// ✅ GLOBAL VARIABLE (TOP LA IRUKANUM)
var isSending = false;

document.addEventListener("DOMContentLoaded", () => {

    let input = document.getElementById("userInput");

    // ✅ ENTER KEY
    if (input) input.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

});


// ✅ MAIN FUNCTION
async function sendMessage() {

    if (isSending) return;
    isSending = true;

    let input = document.getElementById("userInput");
    let message = input.value.trim();

    if (!message) {
        isSending = false;
        return;
    }

    let chatBox = document.getElementById("chatBox");

    // 🟢 USER MESSAGE
    let userMsg = document.createElement("div");
    userMsg.className = "user-msg";
    userMsg.innerText = message;
    chatBox.appendChild(userMsg);

    input.value = "";

    // 🔥 BOT MESSAGE CREATE (IMPORTANT FIX)
    let botMsg = document.createElement("div");
    botMsg.className = "bot-msg";
    botMsg.innerText = "Typing...";
    chatBox.appendChild(botMsg);

    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        let res = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        let data = await res.json();

        // ✅ UPDATE BOT MESSAGE
        botMsg.innerText = data.reply;

    } catch (err) {
        console.error(err);
        botMsg.innerText = "⚠️ Error sending message";
    }

    isSending = false;
}
/* -- EMERGENCY SOS LOGIC -- */
function findHospitals() {
    if (!navigator.geolocation) {
        window.open('https://www.google.com/maps/search/emergency+hospitals+near+me', '_blank');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            window.open(`https://www.google.com/maps/search/emergency+hospitals+near+me/@${lat},${lng},14z`, '_blank');
        },
        (error) => {
            console.warn('Geolocation failed or denied:', error);
            window.open('https://www.google.com/maps/search/emergency+hospitals+near+me', '_blank');
        }
    );
}

function findPharmacies() {
    if (!navigator.geolocation) {
        window.open('https://www.google.com/maps/search/pharmacies+near+me', '_blank');
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            window.open(`https://www.google.com/maps/search/pharmacies+near+me/@${lat},${lng},14z`, '_blank');
        },
        (error) => {
            window.open('https://www.google.com/maps/search/pharmacies+near+me', '_blank');
        }
    );
}

function calculateBMI() {
    const weight = parseFloat(document.getElementById('bmi-weight').value);
    const height = parseFloat(document.getElementById('bmi-height').value) / 100;
    const result = document.getElementById('bmi-result');
    
    if (!weight || !height) {
        result.style.display = 'block';
        result.innerHTML = '<span style="color:#ff8080">⚠️ Please enter valid weight and height.</span>';
        return;
    }
    
    const bmi = (weight / (height * height)).toFixed(1);
    let category = "";
    let color = "";
    let advice = "";
    
    if (bmi < 18.5) { category = "Underweight"; color = "#ffd166"; advice = "Consider a high-protein diet and strength training."; }
    else if (bmi < 25) { category = "Normal weight"; color = "#00ffb3"; advice = "Great job! Maintain your balanced diet and active lifestyle."; }
    else if (bmi < 30) { category = "Overweight"; color = "#ff9f43"; advice = "Try to incorporate 30 mins of cardio 5 days a week."; }
    else { category = "Obese"; color = "#ff6b6b"; advice = "Consult a nutritionist and focus on calorie-deficit meals."; }
    
    result.style.display = 'block';
    result.innerHTML = `
        <div style="font-size:18px; font-weight:700; margin-bottom:10px">Your BMI: <span style="color:${color}">${bmi}</span></div>
        <div style="font-size:14px; margin-bottom:12px">Category: <b style="color:${color}">${category}</b></div>
        <div style="font-size:13px; color:rgba(255,255,255,0.7); line-height:1.5">💡 <b>Advice:</b> ${advice}</div>
    `;
}



