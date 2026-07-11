# Seeroo Travels Attock - Project Brief 🌄

Is file men hum ne is project ke abhi tak ke saare features, structures aur designs ko Roman Urdu aur English men tafseel se brief kiya hai taake aap ko is ka mukammal andaza ho sake.

---

## 📁 Project Structure (Kaise Files Bahi Hain)

Hum ne project ko bilkul clean aur modular rakha hai:
* **`index.html`**: Poore website ki structure aur html skeleton. Is men total **16 sections** hain.
* **`index.css`**: Design system aur stylings. Is men colors, animations, glassmorphism aur responsive grids shamil hain.
* **`app.js`**: Website ka dimagh (logic). Is men Pricing Calculator, Seat Checker, Form Modals, Invoice Generator aur **AI Chat Agent** ki logic hai.
* **`assets/`**: Is folder men hum ne tour ki visual images aur testimonials ke liye custom Pakistani family faces save kiye hain.

---

## 🎨 Visuals aur Design Aesthetics (Kysa Kysa Shamil Hai)

Hum ne brand details ke mutabiq nihayat premium aur high-conversion design banaya hai:

1. **Color Palette (Colors Ka Intekhab)**:
   * **Primary Dark**: Deep Forest Green (`#0E2E24`) - Main dark background aur footer ke liye.
   * **Secondary**: Emerald Green (`#1F6F54`) - Buttons, icons aur active links ke liye.
   * **Accent**: Warm Sunset Orange (`#F4A261`) - CTA highlight aur tags ke liye.
   * **Neutral Light**: Soft Sand (`#F8F5F0`) - Clean light sections ke liye.

2. **Lighting aur Textures**:
   * Pure flat backgrounds ke bajaye hum ne **atmospheric radial gradients (light glow)** aur **gradient mesh overlay** ka istemal kiya hai.
   * Backgrounds men halki **mountain topographic SVG texture** dali hai jo paharon ka premium vibe deti hai.

3. **Typography (Fonts pairing)**:
   * **Plus Jakarta Sans** (grotesque sans-serif) body text aur main headlines ke liye.
   * **Cormorant Garamond** (serif font) hero section ke italics word (*Escape*) ke liye taake standard look aye.
   * **Montserrat, Roboto, Poppins ko mukammal ban (block) kiya gaya hai.**

---

## 🧱 Shamil Sections (Brief of 16 Sections)

Website ko conversion-focused rakhne ke liye 16 sections shamil hain:

1. **Header (Navbar)**: Simple aur high-contrast nav text (Home, Tours, About, Contact, FAQ) aur ek primary "Book Seat" button ke sath (sticky nahi hai, height 72px hai).
2. **Hero Section**: Siri Paye / Shogran ki visual background image ke upar dark mesh aur green light glow ke sath. CTA Buttons ("Book My Seat" aur "Chat With Travel Agent") aur safety trust strip.
3. **Trust Strip (Marquee Scroll)**: Facebook reviews, Instagram family community aur safety record ka horizontal auto-scrolling marquee.
4. **Stats Counter**: 500+ happy travelers, 100% safe family track aur pickup locations ka metric card grid.
5. **Feature Bento Grid (Zero Gaps)**: 6-column modular grid jo baghair kisi khali space ya gaps ke aapas men jura hua hai. Is men large 2x2 AI Assistant card aur surrounding smaller cards (AC transport, meals, family environment, etc.) hain.
6. **Signature Tours (Available Tours)**: Two-column clean list cards:
   * **Shogran & Siri Paye Meadows** (18 July 2026, Rs. 4,500)
   * **Siran Valley & Khanpur Dam** (25 July 2026, Rs. 3,700)
7. **Departure City Selector & Calculator**: Users apne shehar (Attock, Wah, Kamra, Taxila) ke hisab se pickup location aur timing dekh sakte hain. Seat counter bar se real-time pricing calculate hoti hai.
8. **How It Works (3 Steps)**: Choose Tour -> Confirm Seats -> Travel & Enjoy. Subtle step descriptions (e.g. `Step 1 of 3`) ke sath.
9. **Brand Philosophy**: Family safety aur female groups ke safety assurance ki detailed story aur side visual frame.
10. **Social Proof (Testimonials)**: 3 realistic family testimonials jin men real Pakistani family avatars aur star ratings shamil hain.
11. **Meet Your Personal AI Travel Assistant (Showcase)**: AI assistant ke features ka detailed grid aur side par **Live Embed Chat Interface**.
12. **Safety & Trust Assurance Grid**: 4 pillars (First Aid, Verified Drivers, Safe for Families, Pickup Locations) ke icons aur details.
13. **Pre-Trip Packing Guide**: Weekend tour par kya sath le kar ana chahiye (shoes, warm shawl, CNIC, umbrella) us ka visual checklist box.
14. **FAQ Accordion**: 5 expandable boxes jo click karne par smooth sliding rotation animation ke sath open hote hain.
15. **Final Booking CTA**: Hero section se matching bold color card jo booking seats finalize karne ke liye user ko push karta hai.
16. **Footer**: Clean layout jis men quick links, contact info (phone/email/address) aur copywrite details shamil hain.

---

## ⚡ Interactive Engine & AI Booking Bot (Kise Kaam Karta Hai)

Is project ka sab se mazedaar hissa dynamic features hain jo bina reload ke kaam karte hain:

* **Real-time Price & Discount Calculator**: 
  Agar user seats barhata hai to base fare khud hi barhta hai. Group bookings ke rules automated hain:
  * **5 se 9 seats** par **5%** discount milta hai.
  * **10 ya us se zyada seats** par **10%** discount lagta hai.
  * Discount amount aur final total khud-ba-khud show hote hain.
  
* **Live Simulated AI Travel Agent (Seeroo Bot)**:
  * Website ke bottom right corner men floating widget hai aur page ke darmiyan men embedded widget.
  * User "Shogran", "Siran Valley", "seats check", ya "discount" likh kar bot se chat kar sakta hai.
  * Bot foran details deta hai, seat availability checks simulate karta hai (e.g., "12 seats remaining for Shogran"), aur "book" likhne par checkout modal open kar deta hai.

* **Dynamic Invoice & Receipt Generator**:
  * Jaise hi user booking modal fill kar ke submit karta hai, JavaScript background men unique **Invoice ID** (`SR-XXXXXX`) generate karta hai.
  * Modal men ek professional invoice receipt ati hai jis men pricing, pick-up shehar aur timing, lead names aur advance deposit requirements show hoti hain.
  * User **Print / Save PDF** dabaye to browser print screen open ho jati hai jo sirf receipt print karti hai.
  * **Send to WhatsApp** dabaye to ye ek text message create kar ke direct customer care ke WhatsApp number par forward kar deta hai taake seats confirm ho saken.

---

*Brief ready by Antigravity AI Coding Assistant.* 🌄
