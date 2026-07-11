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
let isBookingConfirmed = false;

// Initialize state on page load
document.addEventListener("DOMContentLoaded", () => {
  const threadId = getOrGenerateThreadId();
  const confirmed = localStorage.getItem("seeroo_booking_confirmed_" + threadId);
  if (confirmed === "true") {
    isBookingConfirmed = true;
    setTimeout(disableChatInput, 200);
  }
});

function getOrGenerateThreadId() {
  let threadId = localStorage.getItem("seeroo_thread_id");
  if (!threadId) {
    // Generate simple unique thread UUID format
    threadId = "thread_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now();
    localStorage.setItem("seeroo_thread_id", threadId);
  }
  return threadId;
}

function disableChatInput() {
  const embedInput = document.getElementById("chatEmbedInput");
  const embedSend = document.getElementById("chatEmbedSend");
  const floatingInput = document.getElementById("chatFloatingInput");
  const floatingSend = document.getElementById("chatFloatingSend");
  
  if (embedInput) {
    embedInput.disabled = true;
    embedInput.placeholder = "Booking session locked.";
  }
  if (embedSend) embedSend.disabled = true;
  if (floatingInput) {
    floatingInput.disabled = true;
    floatingInput.placeholder = "Booking session locked.";
  }
  if (floatingSend) floatingSend.disabled = true;
}

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

// Show animated typing indicator bubble
function showTypingIndicator(target) {
  const bodyId = target === "embed" ? "chatEmbedBody" : "chatFloatingBody";
  const body = document.getElementById(bodyId);
  if (!body) return null;

  const msgDiv = document.createElement("div");
  msgDiv.className = "chat-msg bot typing-indicator-msg";
  msgDiv.innerHTML = `<p><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></p>`;
  
  body.appendChild(msgDiv);
  body.scrollTop = body.scrollHeight;
  return msgDiv;
}

// Append interactive success cards inside the chat transcript
function appendBookingSuccessCard(target, bookingId) {
  const bodyId = target === "embed" ? "chatEmbedBody" : "chatFloatingBody";
  const body = document.getElementById(bodyId);
  if (!body) return;

  const cardDiv = document.createElement("div");
  cardDiv.className = "booking-success-card-chat";
  cardDiv.innerHTML = `
    <h5 style="color:#0f5132; margin:0 0 6px 0; font-size:14px; font-weight:700; display:flex; align-items:center; gap:6px;">
      <i data-lucide="check-circle" style="width:16px; height:16px; color:#198754;"></i> Booking Confirmed!
    </h5>
    <p style="font-size:12px; margin:0 0 12px 0; color:#444; line-height:1.4;">
      Your family tour has been committed to our database under ID: <strong>#${bookingId.substring(0, 8).toUpperCase()}</strong>.
    </p>
    <div style="display:flex; flex-direction:column; gap:6px;">
      <button class="btn-success-action-chat" onclick="openInvoiceFromBookingId('${bookingId}')">
        <i data-lucide="file-text" style="width:14px; height:14px;"></i> View Booking Details
      </button>
      <button class="btn-success-action-chat" onclick="printInvoice()">
        <i data-lucide="printer" style="width:14px; height:14px;"></i> Print Invoice
      </button>
      <button class="btn-success-action-chat" onclick="shareWhatsAppFromCard('${bookingId}')">
        <i data-lucide="send" style="width:14px; height:14px;"></i> Share via WhatsApp
      </button>
    </div>
  `;
  body.appendChild(cardDiv);
  body.scrollTop = body.scrollHeight;

  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
}

// Parse user input and query real chat API endpoint
function handleUserMsg(target, text) {
  if (!text.trim()) return;
  if (isBookingConfirmed) {
    appendMessage(target, "bot", "This booking session is completed and locked. Please start a new session by clearing your cache or reloading.");
    return;
  }
  
  // Clear input field
  const inputId = target === "embed" ? "chatEmbedInput" : "chatFloatingInput";
  const sendId = target === "embed" ? "chatEmbedSend" : "chatFloatingSend";
  const input = document.getElementById(inputId);
  const sendBtn = document.getElementById(sendId);
  
  if (input) input.value = "";
  
  // Disable inputs to prevent duplicate sends
  if (input) input.disabled = true;
  if (sendBtn) sendBtn.disabled = true;

  // Append user message
  appendMessage(target, "user", text);

  // Show typing animation
  const typingIndicator = showTypingIndicator(target);
  
  const threadId = getOrGenerateThreadId();

  // Handle timeout (15s limit)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  fetch("/api/v1/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      thread_id: threadId,
      message: text
    }),
    signal: controller.signal
  })
  .then(response => {
    clearTimeout(timeoutId);
    if (typingIndicator) typingIndicator.remove();
    
    // Enable inputs
    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    if (input) input.focus();
    
    if (response.status === 429) {
      appendMessage(target, "bot", "You're sending messages too fast. Please wait a moment.");
      return null;
    }
    if (!response.ok) {
      throw new Error("HTTP error status: " + response.status);
    }
    return response.json();
  })
  .then(data => {
    if (!data) return;

    if (data.error) {
      if (data.error.code === "RATE_LIMIT_EXCEEDED") {
        appendMessage(target, "bot", "You're sending messages too fast. Please wait a moment.");
      } else {
        appendMessage(target, "bot", "Temporary issue. Please try again.");
      }
      return;
    }

    // Output live response reply
    appendMessage(target, "bot", data.reply);

    // Confirmation guides
    if (data.requires_confirmation) {
      updateSuggestions(target, ["Confirm Booking", "Check seat availability", "Cancel Booking"]);
    } else {
      updateSuggestions(target, ["Check seats", "Group discounts", "Main Menu"]);
    }

    // Success invoice triggers
    if (data.booking_id) {
      isBookingConfirmed = true;
      localStorage.setItem("seeroo_booking_confirmed_" + threadId, "true");
      disableChatInput();
      appendBookingSuccessCard(target, data.booking_id);
    }
  })
  .catch(err => {
    clearTimeout(timeoutId);
    if (typingIndicator) typingIndicator.remove();
    
    if (input) input.disabled = false;
    if (sendBtn) sendBtn.disabled = false;
    
    if (err.name === "AbortError") {
      appendMessage(target, "bot", "Connection timed out. Please check your internet connection and try again.");
    } else {
      appendMessage(target, "bot", "Temporary issue. Please try again.");
    }
  });
}

// Fetch booking records and open modal invoice
function openInvoiceFromBookingId(bookingId) {
  fetch(`/api/v1/bookings/${bookingId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error("Booking record not found.");
      }
      return response.json();
    })
    .then(data => {
      const invoiceId = "SR-" + data.id.substring(0, 8).toUpperCase();
      const tourDate = data.tour ? data.tour.departure_date : "TBD";
      const tourName = data.tour ? data.tour.tour_name : "Tour Destination";
      const pickupPoint = PICKUP_DATA[data.pickup_city] ? PICKUP_DATA[data.pickup_city].location : "Main Chowk";
      const pickupTime = PICKUP_DATA[data.pickup_city] ? PICKUP_DATA[data.pickup_city].time : "05:00 AM";
      const leadName = data.user ? data.user.full_name : "Traveler";
      const leadPhone = data.user ? data.user.phone : "WhatsApp Contact";
      
      const pricing = computePricing(data.price_per_head, data.seats);
      const advanceDue = data.seats * 1000;
      const remainingDue = data.total_price - advanceDue;
      
      currentBookingData = {
        invoiceId,
        tourName,
        tourDate,
        seats: data.seats,
        city: data.pickup_city,
        pickupPoint,
        pickupTime,
        name: leadName,
        phone: leadPhone,
        cnic: "Invoiced",
        unitPrice: data.price_per_head,
        rawTotal: pricing.rawTotal,
        discountPct: pricing.discountPct,
        discountAmt: pricing.discountAmt,
        finalTotal: data.total_price,
        advanceDue,
        remainingDue
      };

      const receiptHTML = `
        <div class="invoice-receipt">
          <div class="receipt-header">
            <h4 class="receipt-title">SEEROO TRAVELS ATTOCK</h4>
            <p style="font-size:12px; color:rgba(0,0,0,0.5);">Weekend Escapes for Local Families</p>
            <span class="receipt-status">${data.booking_status.toUpperCase()}</span>
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
      const invoiceModal = document.getElementById("invoiceModal");
      if (invoiceModal) invoiceModal.classList.add("active");
      
      if (typeof lucide !== 'undefined') {
        lucide.createIcons();
      }
    })
    .catch(err => {
      alert("Failed to load invoice details: " + err.message);
    });
}

// Redirect to WhatsApp sharing details from invoice card
function shareWhatsAppFromCard(bookingId) {
  fetch(`/api/v1/bookings/${bookingId}`)
    .then(response => response.json())
    .then(data => {
      const invoiceId = "SR-" + data.id.substring(0, 8).toUpperCase();
      const tourDate = data.tour ? data.tour.departure_date : "TBD";
      const tourName = data.tour ? data.tour.tour_name : "Tour Destination";
      const pickupPoint = PICKUP_DATA[data.pickup_city] ? PICKUP_DATA[data.pickup_city].location : "Main Chowk";
      const pickupTime = PICKUP_DATA[data.pickup_city] ? PICKUP_DATA[data.pickup_city].time : "05:00 AM";
      const leadName = data.user ? data.user.full_name : "Traveler";
      const leadPhone = data.user ? data.user.phone : "WhatsApp Contact";
      const advanceDue = data.seats * 1000;
      
      const msg = `Assalam-o-Alaikum Seeroo Travels! I want to confirm my family booking. Details:
- Lead Traveler: ${leadName}
- Tour: ${tourName} (${tourDate})
- Seats: ${data.seats}
- Pickup City: ${data.pickup_city} (${pickupPoint})
- Pickup Time: ${pickupTime}
- Total Fare: Rs. ${data.total_price.toLocaleString()}
- Advance Deposit Due: Rs. ${advanceDue.toLocaleString()}
Please send bank details for the deposit transfer! Invoice No: #${invoiceId}`;

      const encodedMsg = encodeURIComponent(msg);
      const whatsappURL = `https://wa.me/923001234567?text=${encodedMsg}`;
      window.open(whatsappURL, "_blank");
    })
    .catch(err => {
      alert("Failed to open WhatsApp share: " + err.message);
    });
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
