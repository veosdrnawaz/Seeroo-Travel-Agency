// Initialize Lucide Icons
document.addEventListener("DOMContentLoaded", () => {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // Initialize FAQ Accordions
  const faqTriggers = document.querySelectorAll(".faq-trigger");
  faqTriggers.forEach(trigger => {
    trigger.addEventListener("click", () => {
      const parent = trigger.parentElement;
      const panel = parent.querySelector(".faq-panel");
      
      // Close other panels
      document.querySelectorAll(".faq-item").forEach(item => {
        if (item !== parent && item.classList.contains("active")) {
          item.classList.remove("active");
          item.querySelector(".faq-panel").style.maxHeight = null;
        }
      });
      
      // Toggle current panel
      parent.classList.toggle("active");
      if (parent.classList.contains("active")) {
        panel.style.maxHeight = panel.scrollHeight + "px";
      } else {
        panel.style.maxHeight = null;
      }
    });
  });

  // Initialize Mobile Menu
  const menuToggle = document.getElementById("menuToggle");
  const navMenu = document.getElementById("navMenu");
  if (menuToggle && navMenu) {
    menuToggle.addEventListener("click", () => {
      navMenu.classList.toggle("active");
    });
    
    // Close menu when clicking nav links
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", () => {
        navMenu.classList.remove("active");
      });
    });
  }

  // Initialize Logistics Calculator
  initCalculator();

  // Setup Chat Listeners
  initChatSystems();

  // Setup Booking Form
  const bookingForm = document.getElementById("bookingForm");
  if (bookingForm) {
    bookingForm.addEventListener("submit", handleBookingSubmit);
  }
});

// ==========================================
// DEPARTURE PICKUP POINTS & ESTIMATOR LOGIC
// ==========================================
const PICKUP_DATA = {
  Attock: { location: "Fawara Chowk (Cantt)", time: "05:00 AM" },
  Wah: { location: "G.T. Road Plaza / Cantt Gate", time: "05:30 AM" },
  Kamra: { location: "Kamra Cantt Gate", time: "04:30 AM" },
  Taxila: { location: "Taxila Main Chowk (Flyover)", time: "06:00 AM" }
};

function initCalculator() {
  const citySelector = document.getElementById("citySelector");
  const calcTourSelect = document.getElementById("calcTourSelect");
  const seatVal = document.getElementById("seatVal");
  const seatDec = document.getElementById("seatDec");
  const seatInc = document.getElementById("seatInc");
  const calcBookBtn = document.getElementById("calcBookBtn");

  let activeCity = "Attock";

  if (citySelector) {
    const buttons = citySelector.querySelectorAll(".city-btn");
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeCity = btn.getAttribute("data-city");
        
        // Update pickup info
        const pickupText = document.getElementById("pickupText");
        if (pickupText) {
          pickupText.innerHTML = `<strong>${activeCity}:</strong> ${PICKUP_DATA[activeCity].location} (Departure: ${PICKUP_DATA[activeCity].time})`;
        }
        
        calculateTotal();
      });
    });
  }

  if (seatDec && seatVal) {
    seatDec.addEventListener("click", () => {
      let val = parseInt(seatVal.value);
      if (val > 1) {
        seatVal.value = val - 1;
        calculateTotal();
      }
    });
  }

  if (seatInc && seatVal) {
    seatInc.addEventListener("click", () => {
      let val = parseInt(seatVal.value);
      if (val < 30) {
        seatVal.value = val + 1;
        calculateTotal();
      }
    });
  }

  if (calcTourSelect) {
    calcTourSelect.addEventListener("change", calculateTotal);
  }

  if (calcBookBtn) {
    calcBookBtn.addEventListener("click", () => {
      const tourName = calcTourSelect.options[calcTourSelect.selectedIndex].getAttribute("data-tour-name");
      const price = parseInt(calcTourSelect.value);
      const seats = parseInt(seatVal.value);
      const tourDate = tourName.includes("Shogran") ? "18 July 2026" : "25 July 2026";
      
      startBooking(tourName, price, tourDate, seats, activeCity);
    });
  }

  // Run initial calculation
  calculateTotal();
}

function calculateTotal() {
  const calcTourSelect = document.getElementById("calcTourSelect");
  const seatVal = document.getElementById("seatVal");
  
  if (!calcTourSelect || !seatVal) return;

  const pricePerHead = parseInt(calcTourSelect.value);
  const seats = parseInt(seatVal.value);
  
  const pricing = computePricing(pricePerHead, seats);

  // Update UI elements
  document.getElementById("calcCount").textContent = seats;
  document.getElementById("calcBase").textContent = pricePerHead.toLocaleString();
  document.getElementById("calcRawTotal").textContent = `Rs. ${(pricePerHead * seats).toLocaleString()}`;

  const discountRow = document.getElementById("discountRow");
  if (pricing.discountPct > 0) {
    discountRow.style.display = "flex";
    document.getElementById("calcDiscountPct").textContent = pricing.discountPct;
    document.getElementById("calcDiscountVal").textContent = `-Rs. ${pricing.discountAmt.toLocaleString()}`;
  } else {
    discountRow.style.display = "none";
  }

  document.getElementById("calcFinalTotal").textContent = `Rs. ${pricing.finalTotal.toLocaleString()}`;
}

// Global helper to calculate group pricing rules
function computePricing(pricePerHead, seats) {
  let discountPct = 0;
  if (seats >= 10) {
    discountPct = 10;
  } else if (seats >= 5) {
    discountPct = 5;
  }
  
  const rawTotal = pricePerHead * seats;
  const discountAmt = Math.round(rawTotal * (discountPct / 100));
  const finalTotal = rawTotal - discountAmt;
  
  return {
    rawTotal,
    discountPct,
    discountAmt,
    finalTotal
  };
}


// ==========================================
// INTERACTIVE SIMULATED AI TRAVEL AGENT
// ==========================================
let currentChatTour = null;
let currentChatSeats = null;

function initChatSystems() {
  // 1. Embedded chat elements
  const chatEmbedSend = document.getElementById("chatEmbedSend");
  const chatEmbedInput = document.getElementById("chatEmbedInput");
  
  if (chatEmbedSend && chatEmbedInput) {
    chatEmbedSend.addEventListener("click", () => {
      handleUserMsg("embed", chatEmbedInput.value);
    });
    chatEmbedInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        handleUserMsg("embed", chatEmbedInput.value);
      }
    });
  }

  // 2. Floating chat elements
  const chatFloatingSend = document.getElementById("chatFloatingSend");
  const chatFloatingInput = document.getElementById("chatFloatingInput");
  
  if (chatFloatingSend && chatFloatingInput) {
    chatFloatingSend.addEventListener("click", () => {
      handleUserMsg("floating", chatFloatingInput.value);
    });
    chatFloatingInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        handleUserMsg("floating", chatFloatingInput.value);
      }
    });
  }
}

// Open / Close Floating Widget
function openChat() {
  const container = document.getElementById("floatingChatContainer");
  if (container) {
    container.classList.add("active");
  }
}

function closeChat() {
  const container = document.getElementById("floatingChatContainer");
  if (container) {
    container.classList.remove("active");
  }
}

// User clicks suggestions
function sendSuggest(text) {
  handleUserMsg("embed", text);
}

function sendSuggestFloating(text) {
  handleUserMsg("floating", text);
}

// Append msg to target body
function appendMessage(target, sender, text) {
  const bodyId = target === "embed" ? "chatEmbedBody" : "chatFloatingBody";
  const body = document.getElementById(bodyId);
  if (!body) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = `chat-msg ${sender}`;
  
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  msgDiv.innerHTML = `<p>${text}</p><span class="msg-time">${time}</span>`;
  
  body.appendChild(msgDiv);
  body.scrollTop = body.scrollHeight;
}

// Parse user input and respond
function handleUserMsg(target, text) {
  if (!text.trim()) return;
  
  // Clear input field
  const inputId = target === "embed" ? "chatEmbedInput" : "chatFloatingInput";
  const input = document.getElementById(inputId);
  if (input) input.value = "";

  // Append user message
  appendMessage(target, "user", text);

  // Bot response timeout
  setTimeout(() => {
    const response = generateBotResponse(text);
    appendMessage(target, "bot", response.reply);
    
    // If response prompts tour selection or booking, update internal variables
    if (response.tour) currentChatTour = response.tour;
    if (response.seats) currentChatSeats = response.seats;
    
    // Auto-update suggestions based on context
    updateSuggestions(target, response.suggestions);
  }, 750);
}

// AI Rules Engine (Simulating NLU parser)
function generateBotResponse(input) {
  const text = input.toLowerCase();
  
  // 1. Greetings
  if (text.includes("hello") || text.includes("hi") || text.includes("assalam") || text.includes("aoa") || text.includes("hey")) {
    return {
      reply: "Assalam-o-Alaikum! 🌄 Seeroo Bot at your service. I organize safe, premium, family-only short trips from Attock, Wah, Taxila, and Kamra. You can ask about our upcoming Shogran and Siran Valley trips!",
      suggestions: ["Tell me about Shogran", "Tell me about Siran Valley", "Check seats"]
    };
  }

  // 2. Shogran Meadows info
  if (text.includes("shogran") || text.includes("siri paye") || text.includes("meadows")) {
    return {
      tour: "Shogran & Siri Paye Meadows",
      reply: "Our Shogran & Siri Paye Meadows trip takes place on Saturday, 18 July 2026. Pricing: Rs. 4,500/head. It includes AC Saloon coaster transit, breakfast & dinner, basic first aid, and the Kiwai-to-Siri Paye jeep transport! Would you like to check seat availability or calculate pricing for your group?",
      suggestions: ["Calculate Shogran pricing", "Check Shogran seats", "Go back"]
    };
  }

  // 3. Siran Valley / Khanpur Dam info
  if (text.includes("siran") || text.includes("khanpur") || text.includes("dam") || text.includes("valley")) {
    return {
      tour: "Siran Valley & Khanpur Dam",
      reply: "Our Siran Valley & Khanpur Dam tour takes place on Saturday, 25 July 2026. Pricing: Rs. 3,700/head. Inclusions: AC transit, breakfast & dinner, tour guides, and boating at Khanpur Dam lake! Would you like to calculate your group price or check seats?",
      suggestions: ["Calculate Siran pricing", "Check Siran seats", "Go back"]
    };
  }

  // 4. Seat availability checker
  if (text.includes("seat") || text.includes("availability") || text.includes("remaining") || text.includes("slots")) {
    return {
      reply: "Checking seat inventories... 🔍 <br>🟢 <strong>Shogran Siri Paye (18 July):</strong> 12 seats remaining.<br>🟢 <strong>Siran Valley & Khanpur (25 July):</strong> 15 seats remaining.<br>How many seats are you looking to reserve?",
      suggestions: ["Book for 4 people", "Book for 8 people", "Ask about discounts"]
    };
  }

  // 5. Discount query
  if (text.includes("discount") || text.includes("group") || text.includes("family price") || text.includes("reduction")) {
    return {
      reply: "Yes, we offer special group/family discounts! 🏷️<br>• <strong>5 to 9 seats:</strong> 5% discount.<br>• <strong>10 or more seats:</strong> 10% discount.<br>Tell me how many seats you need, and I'll calculate the final quote!",
      suggestions: ["Price for 6 people", "Price for 12 people", "Main Menu"]
    };
  }

  // 6. Pricing calculations parser
  const seatMatch = text.match(/(\d+)\s*(seat|people|person|head|member|passenger)/);
  if (seatMatch || text.includes("calculate") || text.includes("price for")) {
    let seatsNum = 4; // Default fallback
    if (seatMatch) {
      seatsNum = parseInt(seatMatch[1]);
    } else {
      // Look for any isolated number
      const numMatch = text.match(/\b(\d+)\b/);
      if (numMatch) seatsNum = parseInt(numMatch[1]);
    }
    
    // Determine tour context
    let selectedTour = currentChatTour || "Shogran & Siri Paye Meadows";
    let basePrice = selectedTour.includes("Siran") ? 3700 : 4500;
    
    const pricing = computePricing(basePrice, seatsNum);
    
    let discountMsg = pricing.discountPct > 0 
      ? `🎉 Congratulations! A ${pricing.discountPct}% group discount has been applied (saved Rs. ${pricing.discountAmt.toLocaleString()}).` 
      : `No group discount applied (discounts start at 5+ seats).`;

    return {
      tour: selectedTour,
      seats: seatsNum,
      reply: `Here is the pricing breakdown for <strong>${seatsNum} seats</strong> on the <strong>${selectedTour}</strong> tour:<br>• Base Rate: Rs. ${basePrice.toLocaleString()} / head<br>• Subtotal: Rs. ${pricing.rawTotal.toLocaleString()}<br>• ${discountMsg}<br>👉 <strong>Total Estimated Price: Rs. ${pricing.finalTotal.toLocaleString()}</strong><br><br>Would you like me to open the booking reservation form now?`,
      suggestions: ["Yes, open booking form", "Change tour destination", "Main Menu"]
    };
  }

  // 7. Booking triggers
  if (text.includes("book") || text.includes("reserve") || text.includes("yes") || text.includes("proceed") || text.includes("form")) {
    let selectedTour = currentChatTour || "Shogran & Siri Paye Meadows";
    let basePrice = selectedTour.includes("Siran") ? 3700 : 4500;
    let seatsNum = currentChatSeats || 2;
    let tourDate = selectedTour.includes("Shogran") ? "18 July 2026" : "25 July 2026";
    
    // Trigger modal launch
    setTimeout(() => {
      startBooking(selectedTour, basePrice, tourDate, seatsNum, "Attock");
    }, 500);

    return {
      reply: `Opening the reservation form for <strong>${selectedTour}</strong> with <strong>${seatsNum} seats</strong>. Please fill out your details in the modal that just appeared!`,
      suggestions: ["Check other tours", "Main Menu"]
    };
  }

  // 8. Go back / main menu
  if (text.includes("back") || text.includes("menu") || text.includes("start over")) {
    return {
      reply: "How can I assist you? You can ask about Shogran, check seat availability, or calculate pricing directly.",
      suggestions: ["Tell me about Shogran", "Tell me about Siran Valley", "Check seats"]
    };
  }

  // 9. Fallback
  return {
    reply: "I'm happy to help with that! However, I work best when answering questions about our signature tours (Shogran Meadows / Siran Valley), picking up locations, checking seats, or calculating group discounts. Please type a specific question, or click one of the suggested buttons below.",
    suggestions: ["Tell me about Shogran", "Check seat availability", "Main Menu"]
  };
}

// Update chat suggestions in HTML
function updateSuggestions(target, suggestions) {
  const containerId = target === "embed" ? "chatSuggestions" : "chatSuggestionsFloating";
  const container = document.getElementById(containerId);
  if (!container || !suggestions) return;

  container.innerHTML = "";
  suggestions.forEach(s => {
    const btn = document.createElement("button");
    btn.className = "suggest-btn";
    btn.textContent = s;
    if (target === "embed") {
      btn.onclick = () => sendSuggest(s);
    } else {
      btn.onclick = () => sendSuggestFloating(s);
    }
    container.appendChild(btn);
  });
}


// ==========================================
// BOOKING FORM AND INVOICE GENERATOR
// ==========================================
let currentBookingData = null;

function startBooking(tourName, pricePerHead, tourDate, seats = 2, city = "Attock") {
  const modal = document.getElementById("bookingModal");
  if (!modal) return;

  // Pre-fill fields
  document.getElementById("bookTourName").value = tourName;
  document.getElementById("bookTourDate").value = tourDate;
  document.getElementById("bookSeats").value = seats;
  document.getElementById("bookCity").value = city;

  // Pre-fill prices
  updateModalPricing(pricePerHead, seats);

  // Set event listener for seat changes in modal
  const seatsInput = document.getElementById("bookSeats");
  seatsInput.oninput = () => {
    let s = parseInt(seatsInput.value) || 1;
    if (s < 1) s = 1;
    if (s > 30) s = 30;
    seatsInput.value = s;
    updateModalPricing(pricePerHead, s);
  };

  modal.classList.add("active");
  
  // Store temp pricing vars
  modal.setAttribute("data-unit-price", pricePerHead);
}

function updateModalPricing(unitPrice, seats) {
  const pricing = computePricing(unitPrice, seats);
  
  document.getElementById("modalUnitPrice").textContent = `Rs. ${unitPrice.toLocaleString()}`;
  
  const discountRow = document.getElementById("modalDiscountRow");
  if (pricing.discountPct > 0) {
    discountRow.style.display = "flex";
    document.getElementById("modalDiscountPct").textContent = pricing.discountPct;
    document.getElementById("modalDiscountVal").textContent = `-Rs. ${pricing.discountAmt.toLocaleString()}`;
  } else {
    discountRow.style.display = "none";
  }
  
  document.getElementById("modalTotalPrice").textContent = `Rs. ${pricing.finalTotal.toLocaleString()}`;
}

function closeBookingModal() {
  const modal = document.getElementById("bookingModal");
  if (modal) modal.classList.remove("active");
}

function handleBookingSubmit(e) {
  e.preventDefault();
  
  const tourName = document.getElementById("bookTourName").value;
  const tourDate = document.getElementById("bookTourDate").value;
  const seats = parseInt(document.getElementById("bookSeats").value);
  const city = document.getElementById("bookCity").value;
  const name = document.getElementById("bookName").value;
  const phone = document.getElementById("bookPhone").value;
  const cnic = document.getElementById("bookCNIC").value;
  
  const modal = document.getElementById("bookingModal");
  const unitPrice = parseInt(modal.getAttribute("data-unit-price"));
  const pricing = computePricing(unitPrice, seats);
  
  const invoiceId = "SR-" + Math.floor(100000 + Math.random() * 900000);
  
  currentBookingData = {
    invoiceId,
    tourName,
    tourDate,
    seats,
    city,
    pickupPoint: PICKUP_DATA[city].location,
    pickupTime: PICKUP_DATA[city].time,
    name,
    phone,
    cnic,
    unitPrice,
    rawTotal: pricing.rawTotal,
    discountPct: pricing.discountPct,
    discountAmt: pricing.discountAmt,
    finalTotal: pricing.finalTotal,
    advanceDue: seats * 1000,
    remainingDue: pricing.finalTotal - (seats * 1000)
  };

  // Generate Receipt HTML
  const receiptHTML = `
    <div class="invoice-receipt">
      <div class="receipt-header">
        <h4 class="receipt-title">SEEROO TRAVELS ATTOCK</h4>
        <p style="font-size:12px; color:rgba(0,0,0,0.5);">Weekend Escapes for Local Families</p>
        <span class="receipt-status">Reservation Drafted</span>
      </div>
      
      <table class="receipt-details-table">
        <tr>
          <td class="label-col">Invoice No.</td>
          <td class="val-col">#${currentBookingData.invoiceId}</td>
        </tr>
        <tr>
          <td class="label-col">Lead Traveler</td>
          <td class="val-col">${currentBookingData.name}</td>
        </tr>
        <tr>
          <td class="label-col">WhatsApp</td>
          <td class="val-col">${currentBookingData.phone}</td>
        </tr>
        <tr>
          <td class="label-col">CNIC No.</td>
          <td class="val-col">${currentBookingData.cnic}</td>
        </tr>
        <tr>
          <td class="label-col">Tour Name</td>
          <td class="val-col">${currentBookingData.tourName}</td>
        </tr>
        <tr>
          <td class="label-col">Departure Date</td>
          <td class="val-col">${currentBookingData.tourDate}</td>
        </tr>
        <tr>
          <td class="label-col">Departure Point</td>
          <td class="val-col">${currentBookingData.city} (${currentBookingData.pickupPoint})</td>
        </tr>
        <tr>
          <td class="label-col">Pickup Time</td>
          <td class="val-col">${currentBookingData.pickupTime}</td>
        </tr>
        <tr>
          <td class="label-col">Seats Booked</td>
          <td class="val-col">${currentBookingData.seats} Seats</td>
        </tr>
      </table>
      
      <div class="receipt-pricing">
        <div class="receipt-pricing-row">
          <span>Fare (${currentBookingData.seats} x Rs. ${currentBookingData.unitPrice.toLocaleString()})</span>
          <span>Rs. ${currentBookingData.rawTotal.toLocaleString()}</span>
        </div>
        ${currentBookingData.discountAmt > 0 ? `
        <div class="receipt-pricing-row" style="color:var(--secondary);">
          <span>Group Discount (${currentBookingData.discountPct}%)</span>
          <span>-Rs. ${currentBookingData.discountAmt.toLocaleString()}</span>
        </div>` : ''}
        <div class="receipt-pricing-row total-row">
          <span>Final Fare</span>
          <span>Rs. ${currentBookingData.finalTotal.toLocaleString()}</span>
        </div>
        
        <hr style="border:0; border-top:1px dashed rgba(0,0,0,0.1); margin:10px 0;">
        
        <div class="receipt-pricing-row" style="font-weight: 600; color: #b84f00;">
          <span>Advance Deposit (Rs. 1000/seat)</span>
          <span>Rs. ${currentBookingData.advanceDue.toLocaleString()}</span>
        </div>
        <div class="receipt-pricing-row" style="font-weight: 600; color: var(--primary-dark);">
          <span>Due at Boarding</span>
          <span>Rs. ${currentBookingData.remainingDue.toLocaleString()}</span>
        </div>
      </div>
      
      <p class="receipt-footer-notes">
        Please share this invoice via WhatsApp to verify your advance seat deposit of Rs. ${currentBookingData.advanceDue.toLocaleString()} and receive final ticket confirmations.
      </p>
    </div>
  `;

  document.getElementById("invoiceReceiptBody").innerHTML = receiptHTML;
  
  // Close booking form, open invoice display
  closeBookingModal();
  
  const invoiceModal = document.getElementById("invoiceModal");
  if (invoiceModal) invoiceModal.classList.add("active");
  
  // Re-create icons for new dynamic modal contents
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

function closeInvoiceModal() {
  const invoiceModal = document.getElementById("invoiceModal");
  if (invoiceModal) invoiceModal.classList.remove("active");
}

function printInvoice() {
  window.print();
}

function shareWhatsApp() {
  if (!currentBookingData) return;
  
  const msg = `Assalam-o-Alaikum Seeroo Travels! I want to confirm my family booking. Details:
- Lead Traveler: ${currentBookingData.name}
- Tour: ${currentBookingData.tourName} (${currentBookingData.tourDate})
- Seats: ${currentBookingData.seats}
- Pickup City: ${currentBookingData.city} (${currentBookingData.pickupPoint})
- Pickup Time: ${currentBookingData.pickupTime}
- Total Fare: Rs. ${currentBookingData.finalTotal.toLocaleString()}
- Advance Deposit Due: Rs. ${currentBookingData.advanceDue.toLocaleString()}
Please send bank details for the deposit transfer! CNIC: ${currentBookingData.cnic}. Invoice No: #${currentBookingData.invoiceId}`;

  const encodedMsg = encodeURIComponent(msg);
  const whatsappURL = `https://wa.me/923001234567?text=${encodedMsg}`;
  window.open(whatsappURL, "_blank");
}
