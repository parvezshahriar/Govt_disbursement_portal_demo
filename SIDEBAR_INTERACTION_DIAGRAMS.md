# 🎨 Sidebar Menu UX Flow & Interaction Diagrams

**Visual Guide to Sidebar Navigation Behavior**

---

## 📊 State Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       USER INTERACTION FLOW                 │
└─────────────────────────────────────────────────────────────┘

                         PAGE LOAD
                            │
                            ▼
                    ┌───────────────┐
                    │ Load Sidebar  │
                    │  loadSidebar()│
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────────────┐
                    │ Check User Role from   │
                    │   localStorage        │
                    └───────┬───────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
            ADMIN      MANAGER       USER
              │           │           │
              └─────┬─────┴─────┬─────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ setActiveSidebarItem()    │
        │ - Read from localStorage  │
        │ - Highlight active item   │
        │ - Open parent submenu     │
        └───────┬───────────────────┘
                │
                ▼
        ┌───────────────────────────┐
        │   SIDEBAR READY           │
        │   For User Interaction    │
        └───────────────────────────┘
```

---

## 🖱️ Click Event Flow

```
USER CLICKS MENU ITEM
         │
         ▼
  ┌──────────────────────┐
  │ onclick Event Fires  │
  │ (handleSidebarClick) │
  └──────────┬───────────┘
             │
             ▼
      ┌────────────────────┐
      │ Check Item Type    │
      └──┬──────────────┬──┐
         │              │  │
         ▼              ▼  ▼
    MAIN ITEM      SUBITEM MAIN
    (no submenu)   (has submenu) (has submenu)
         │              │          │
         ▼              ▼          ▼
    ┌─────────┐   ┌─────────┐  ┌─────────┐
    │ Toggle  │   │ Has Sub?│  │ Already │
    │ Active  │   │         │  │ Open?   │
    │ Class   │   └────┬────┘  └────┬────┘
    └────┬────┘        │            │
         │        YES  │ NO    YES  │ NO
         │             ▼             ▼   ▼
         │        ┌─────────┐   CLOSE OPEN
         │        │ Open    │   SUBMENU SUBMENU
         │        │Submenu  │
         │        │Rotate   │
         │        │Arrow    │
         │        └────┬────┘
         │             │
         └─────────┬───┘
                   │
                   ▼
         ┌──────────────────┐
         │ Navigate to Page │
         │ (navigateToPage) │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │ Show new HTML page   │
         │ Reload Sidebar       │
         │ Restore active state │
         └──────────────────────┘
```

---

## 📂 Menu Hierarchy Diagram

```
┌─────────────────────────────────────────────────────┐
│                     SIDEBAR MENU                    │
└─────────────────────────────────────────────────────┘

├─ BRAND SECTION
│  └─ Logo (logo.png)
│
├─ MENU SECTION
│  ├─ [📊 DASHBOARD] ◄─── Admin Only
│  │
│  ├─ [📋 TASK]
│  │  ├─ 📤 Upload
│  │  └─ 📜 Upload History
│  │
│  ├─ [👤 USER]
│  │  └─ ➕ Create User
│  │
│  ├─ [🔐 SECURITY & ACCESS]
│  │  ├─ 👥 User Management
│  │  └─ 📋 Audit History
│  │
│  └─ [Icons Legend]
│     ├─ 📊 = file-upload icon
│     ├─ 📋 = tasks icon
│     ├─ 👤 = user icon
│     ├─ 🔐 = shield-halved icon
│     ├─ 📤 = file-upload icon
│     ├─ 📜 = history icon
│     └─ + (more icons...)
│
└─ FOOTER SECTION
   └─ ≫ Collapse Toggle (Visual)
```

---

## 🎬 Submenu Toggle Animation

```
INITIAL STATE (Closed)
┌──────────────────────────┐
│ ▶ Task                   │ ◄── Arrow pointing right, opacity 0.8
└──────────────────────────┘


USER HOVERS
┌──────────────────────────┐
│ ▶ Task                   │ ◄── opacity 1.0, background light
└──────────────────────────┘


USER CLICKS
┌──────────────────────────┐
│ ▼ Task                   │ ◄── Arrow rotates 180°
├──────────────────────────┤
│   📤 Upload              │ ◄── Submenu slides down, opacity 1.0
│   📜 Upload History      │
└──────────────────────────┘


ANIMATION TIMING
├─ Arrow rotation:     0.3s ease
├─ Submenu expansion:  0.3s ease
├─ Opacity change:     0.3s ease
└─ Background slide:   0.3s ease
```

---

## 🎨 CSS State Machine

```
.sidebar-item STATES:

┌────────────────────────────────────┐
│  DEFAULT                           │
│  ├─ opacity: 0.8                   │
│  ├─ padding: 12px 15px             │
│  ├─ font-weight: normal            │
│  └─ background: transparent        │
└────────────┬───────────┬───────────┘
             │           │
        HOVER│           │CLICK (Active)
             │           │
   ┌─────────▼──┐    ┌───▼────────────┐
   │  HOVER     │    │   ACTIVE       │
   │ ├─ opacity:│    │ ├─ opacity: 1  │
   │ │   1.0    │    │ ├─ font-weight:│
   │ ├─ scale:  │    │ │   600        │
   │ │ 1.05     │    │ ├─ background: │
   │ ├─ shadow: │    │ │ rgba(w,w,w,  │
   │ │ +box     │    │ │ 0.15)        │
   │ └─ translateX   │ ├─ shadow: +box│
   │   5px      │    │ └─ translateX: │
   └────────────┘    │   5px          │
                     └────────────────┘
```

---

## 📱 Responsive Layout Diagram

### Desktop View (> 1024px)

```
┌─────────────────────────────────────────────────────┐
│                    HEADER (70px)                    │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ SIDEBAR  │                                          │
│  260px   │         MAIN CONTENT AREA                │
│          │                                          │
│ ┌──────┐ │                                          │
│ │ Logo │ │                                          │
│ └──────┘ │                                          │
│          │                                          │
│ [📊 D]   │                                          │
│ [📋 T]   │                                          │
│  ├─ 📤   │                                          │
│  └─ 📜   │                                          │
│ [👤 U]   │                                          │
│  └─ ➕   │                                          │
│ [🔐 S]   │                                          │
│  ├─ 👥   │                                          │
│  └─ 📋   │                                          │
│          │                                          │
│    ≫     │                                          │
└──────────┴──────────────────────────────────────────┘
```

### Tablet View (768px - 1024px)

```
┌─────────────────────────────────────────────────────┐
│         HEADER (70px) w/ Toggle Button              │
├─────────────────────────────────────────────────────┤
│ SIDEBAR    │                                        │
│ 260px      │      MAIN CONTENT AREA                 │
│ (Toggle)   │ (Responsive width)                     │
│            │                                        │
│ [📊 D]     │                                        │
│ [📋 T]     │                                        │
│  ├─ 📤     │                                        │
│  └─ 📜    │                                        │
│            │                                        │
└────────────┴────────────────────────────────────────┘
```

### Mobile View (< 768px)

```
┌────────────────────────────────────┐
│    HEADER (70px) ☰ Toggle          │
├────────────────────────────────────┤
│                                    │
│                                    │
│      MAIN CONTENT AREA             │
│         (Full Width)               │
│                                    │
│                                    │
│                                    │
│                                    │
│                                    │
└────────────────────────────────────┘

[SIDEBAR OVERLAY - appears on toggle]
┌────────────────────────────────────┐
│ Logo                        ✕       │
├────────────────────────────────────┤
│ [📊 Dashboard]                     │
│ ├─ [📋 Task]                       │
│ │ ├─ 📤 Upload                     │
│ │ └─ 📜 Upload History             │
│ ├─ [👤 User]                       │
│ │ └─ ➕ Create User                │
│ └─ [🔐 Security & Access]          │
│   ├─ 👥 User Management           │
│   └─ 📋 Audit History             │
└────────────────────────────────────┘
```

---

## 🔐 Role-Based Visibility Matrix

```
┌─────────────────────┬────────┬─────────┬──────────┐
│  Menu Item          │ ADMIN  │ MANAGER │  USER    │
├─────────────────────┼────────┼─────────┼──────────┤
│ 📊 Dashboard        │   ✓    │    ✗    │    ✗     │
├─────────────────────┼────────┼─────────┼──────────┤
│ 📋 TASK             │   ✓    │    ✓    │    ✓     │
│   ├─ 📤 Upload      │   ✓    │    ✓    │    ✓     │
│   └─ 📜 Upload Hist │   ✓    │    ✓    │    ✓     │
├─────────────────────┼────────┼─────────┼──────────┤
│ 👤 USER             │   ✓    │    ✗    │    ✗     │
│   └─ ➕ Create User  │   ✓    │    ✗    │    ✗     │
├─────────────────────┼────────┼─────────┼──────────┤
│ 🔐 SECURITY & ACCESS│   ✓    │    ✗    │    ✗     │
│   ├─ 👥 User Mgmt   │   ✓    │    ✗    │    ✗     │
│   └─ 📋 Audit Hist  │   ✓    │    ✗    │    ✗     │
└─────────────────────┴────────┴─────────┴──────────┘

Legend:
  ✓ = Visible & Accessible
  ✗ = Hidden & Not Accessible
```

---

## 💾 Data Flow: Navigation

```
USER INTERFACE (Sidebar)
        ▲
        │
        │ 1. Click event
        │
        ▼
┌──────────────────────┐
│ handleSidebarClick   │
└──────────┬───────────┘
           │
           │ 2. Extract page name
           │    from data-page attr
           ▼
┌──────────────────────┐
│ Save to localStorage │
│ activePage: "upload" │
└──────────┬───────────┘
           │
           │ 3. Call navigateToPage
           │
           ▼
┌──────────────────────┐
│ pageMap lookup       │
│ "upload" →           │
│ "image-upload.html"  │
└──────────┬───────────┘
           │
           │ 4. Update window.location
           │
           ▼
┌──────────────────────┐
│ HTTP GET request     │
│ image-upload.html    │
└──────────┬───────────┘
           │
           │ 5. New HTML loads
           │
           ▼
┌──────────────────────┐
│ loadSidebar()        │
│ (in new page)        │
└──────────┬───────────┘
           │
           │ 6. Retrieve activePage
           │    from localStorage
           ▼
┌──────────────────────┐
│ setActiveSidebarItem │
│ - Highlight item     │
│ - Open submenu       │
└──────────────────────┘
```

---

## 🎯 Event Binding Diagram

```
SIDEBAR.HTML (Structure)
        │
        ├─ Menu Item
        │  └─ onclick="handleSidebarClick(this, 'page')"
        │
        └─ Menu Parent (submenu)
           └─ onclick="toggleSubmenu(event, 'menu-id')"

        ▲        ▲
        │        │
        └────┬───┘
             │
        SIDEBAR.JS (Events)
        
        Event Listeners:
        ├─ DOMContentLoaded
        │  └─ Trigger: loadSidebar()
        │
        ├─ Click on menu-item
        │  └─ Trigger: handleSidebarClick()
        │
        └─ Click on submenu-parent
           └─ Trigger: toggleSubmenu()

        ▲
        │
        │ CSS Classes Modified
        │
        SIDEBAR.CSS (Styling)
        
        Class Changes:
        ├─ .active (Add/Remove)
        │  └─ Shows: Highlight + shadow
        │
        ├─ .expanded (Add/Remove)
        │  └─ Rotates: Chevron 180°
        │
        └─ .visible (Add/Remove)
           └─ Shows: Hidden submenus
```

---

## ⚡ Performance Timeline

```
PAGE LOAD TIMELINE
                    
0ms    ┌─ PAGE LOAD STARTS
       │
30ms   ├─ HTML parsed
       │
50ms   ├─ CSS loaded
       │  └─ Sidebar styles applied
       │
80ms   ├─ JavaScript loaded
       │
100ms  ├─ DOMContentLoaded fired
       │  └─ loadSidebar() executed
       │     ├─ Read localStorage
       │     ├─ Insert HTML
       │     └─ Bind event listeners (< 10ms)
       │
120ms  ├─ setActiveSidebarItem() executed
       │  ├─ Query DOM (< 5ms)
       │  ├─ Add .active class (< 2ms)
       │  └─ CSS transitions start
       │
150ms  ├─ CSS animations complete
       │  └─ Sidebar fully interactive
       │
200ms  └─ Page fully ready
        └─ Total time: ~200ms

Performance Budget:
├─ HTML parsing:     < 30ms
├─ CSS parsing:      < 20ms
├─ JS execution:     < 20ms (sidebar.js)
├─ DOM manipulation: < 10ms
└─ Total:            < 100ms (target)
```

---

## 🔍 Debug Flow Chart

```
TROUBLESHOOTING: Menu not responding

START
  │
  ├─ Sidebar visible? 
  │  ├─ NO → Check .sidebar CSS display
  │  └─ YES ↓
  │
  ├─ Menu items visible?
  │  ├─ NO → Check .sidebar-item opacity
  │  └─ YES ↓
  │
  ├─ Click handlers attached?
  │  ├─ Check console for handleSidebarClick
  │  ├─ NO → Check sidebar.js loaded (script tag)
  │  └─ YES ↓
  │
  ├─ localStorage available?
  │  ├─ NO → Check browser privacy mode
  │  └─ YES ↓
  │
  ├─ activePage saved?
  │  ├─ Open DevTools > Application > localStorage
  │  ├─ NO → Check navigateToPage() call
  │  └─ YES ↓
  │
  ├─ Page map contains entry?
  │  ├─ NO → Add entry to pageMap in sidebar.js
  │  └─ YES ↓
  │
  ├─ HTML file exists?
  │  ├─ NO → Create new page file
  │  └─ YES ↓
  │
  └─ Page loads successfully?
     ├─ NO → Check page markup & errors
     └─ YES → Issue resolved ✓
```

---

## 📊 Sidebar Component Dependencies

```
SIDEBAR (Entry Point)
    │
    ├─┬─ sidebar.html
    │ └─ Defines markup structure
    │
    ├─┬─ sidebar.css
    │ └─ Styles & animations
    │     └─ Depends on: Font Awesome 6.4.0
    │
    └─┬─ sidebar.js
      ├─ loadSidebar()
      │  └─ Injects HTML
      │
      ├─ handleSidebarClick()
      │  ├─ Uses localStorage API
      │  └─ Calls navigateToPage()
      │
      ├─ toggleSubmenu()
      │  └─ Modifies DOM classes
      │
      ├─ setActiveSidebarItem()
      │  ├─ Reads localStorage
      │  └─ Modifies DOM classes
      │
      └─ navigateToPage()
         └─ Uses window.location
         
EXTERNAL DEPENDENCIES:
    ├─ Font Awesome CDN (icons)
    ├─ localStorage API (data)
    └─ window.location (navigation)
```

---

## 🎪 Animation Sequence Diagram

```
SUBMENU TOGGLE ANIMATION

Frame 0%
┌─────────────────────────┐
│ ▶ Task    (rotate: 0°)  │
│ opacity: 0.8            │
└─────────────────────────┘

Frame 30%
┌─────────────────────────┐
│ ↘ Task    (rotate: 45°) │
│   📤 Upload             │ ← opacity: 0.3
│   📜 Upload History     │   opacity: 0.3
└─────────────────────────┘

Frame 60%
┌─────────────────────────┐
│ ↓ Task    (rotate: 120°)│
│   📤 Upload             │ ← opacity: 0.7
│   📜 Upload History     │   opacity: 0.7
└─────────────────────────┘

Frame 100%
┌─────────────────────────┐
│ ▼ Task    (rotate: 180°)│  ← active
│   📤 Upload             │  ← opacity: 1.0
│   📜 Upload History     │     opacity: 1.0
└─────────────────────────┘

Duration: 300ms
Easing: ease
```

---

**Sidebar Menu Interaction Diagrams - Complete**  
**Total Diagrams**: 14  
**Last Updated**: February 9, 2026  
**Version**: 1.0.0
