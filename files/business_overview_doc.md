# Business Overview - Photography Studio Management System

**Version:** 1.0  
**Last Updated:** 2025-01-07  
**Document Type:** Business Requirements & Domain Understanding

This document captures the business context, needs, and requirements for the Photography Studio Management System. It serves as the foundation for understanding what we're building and why.

---

## Table of Contents

1. [Business Context](#1-business-context)
2. [Current Situation & Pain Points](#2-current-situation--pain-points)
3. [Business Goals](#3-business-goals)
4. [Users & Stakeholders](#4-users--stakeholders)
5. [Core Business Processes](#5-core-business-processes)
6. [Business Rules & Policies](#6-business-rules--policies)
7. [Future Vision](#9-future-vision)

---

## 1. Business Context

### 1.1 About the Business

**Business Name:** Photography Studio (placeholder name)  
**Business Type:** Professional photography services  
**Location:** Guatemala  
**Team Size:** 8 people (currently growing)  
**Years in Operation:** Established business experiencing rapid growth

### 1.2 Services Offered

The studio provides two main categories of photography services:

**Studio Sessions (In-house):**
- Professional photography (corporate, headshots, portfolio)
- Personal portraits
- Maternity photoshoots
- Family portraits
- Other specialized studio work

**External Sessions (On-location):**
- Event coverage (weddings, parties, celebrations)
- Corporate events
- Fashion/modeling photoshoots
- Outdoor sessions

### 1.3 Current Scale

**Monthly Volume:**
- ~40 studio sessions per month
- ~22 external sessions per month
- **Total: ~62 sessions per month**
- Growing trend over the last 5 months

**Peak Seasons:**
- November-December (holidays, graduations)
- Summer months (better weather, outdoor events)
- Spring (weddings, celebrations)
- Record: 37 external sessions in a single month (November)

**Team Composition:**
- 1 General Manager (also handles coordination)
- 1 Coordinator (also does photography)
- 3 Photographers (5 total including manager + coordinator)
- 3 Editors

**Planned Growth:**
- Adding 1-2 dedicated coordinators
- Reducing manager's operational workload
- Scaling to handle increased demand

---

## 2. Current Situation & Pain Points

### 2.1 Current Tools

**Excel Spreadsheets:**
- Session scheduling
- Client information
- Payment tracking
- Photographer assignments

**Notion Templates:**
- Team coordination
- Task management
- Project tracking

### 2.2 Critical Pain Points

#### 🔴 **Problem 1: Lack of Visibility (HIGHEST PRIORITY)**

**Symptoms:**
- Cannot quickly see agenda availability
- Difficult to assess if they can accept new clients
- Slow response times to client inquiries
- Lost business opportunities while evaluating feasibility

**Impact:**
- Clients go to competitors while waiting for response
- Lost revenue from delayed responses

**Example:**
> "A client contacts us on Monday for a session on Saturday. We need to check if photographers are available, if the studio is free, and coordinate with the team. By the time we respond (sometimes 2-3 days), the client has already hired another studio."

---

#### 🔴 **Problem 2: Double-Booking & Scheduling Conflicts**

**Symptoms:**
- Accidentally confirm two sessions for the same date/time/photographer
- Manual tracking of photographer availability fails
- Human error in Excel (dragging formulas, overwriting cells)

**Impact:**
- Must cancel confirmed sessions
- Angry customers
- Damaged reputation
- Stress on team

**Example:**
> "We confirmed two weddings for October 20th but only realized a week before that we don't have enough photographers. We had to call one client and cancel, who was understandably upset."

---

#### 🔴 **Problem 3: Inefficient Session Evaluation**

**Symptoms:**
- Time-consuming to determine feasibility of serving a client
- Complex manual checks across multiple spreadsheets
- Bottleneck in the initial stages of client acquisition

**Impact:**
- Slow response times
- Team spends excessive time on administrative tasks
- Less time for actual photography work

---

#### 🟡 **Problem 4: Missed Opportunities**

**Symptoms:**
- Sometimes reject clients thinking agenda is full when it's not
- Excel errors (wrong cell, outdated information)
- Conservative booking due to uncertainty

**Impact:**
- Direct revenue loss
- Operating below capacity

---

#### 🟡 **Problem 5: Unclear Responsibilities**

**Symptoms:**
- Confusion about who is responsible for what
- Communication gaps between team members
- Tasks falling through the cracks

**Impact:**
- Inefficiency
- Duplicated efforts
- Missed deadlines

---

### 2.3 What's Working Well

Despite the challenges, some things work:
- ✅ Quality of photography services is excellent
- ✅ Client satisfaction with final products is high
- ✅ Team is skilled and dedicated
- ✅ Business is growing (proof of demand)
- ✅ Basic processes exist (just need better tools)

---

## 3. Business Goals

### 3.1 Primary Goals

**Goal 1: Increase Response Speed**
- **Current:** 2-3 days to respond to client inquiries
- **Target:** Same-day or next-day responses
- **Why:** Capture more clients before they go elsewhere

**Goal 2: Eliminate Scheduling Conflicts**
- **Current:** 2-3 double-bookings or errors per month
- **Target:** Zero scheduling conflicts
- **Why:** Protect reputation and client relationships

**Goal 3: Scale Operations**
- **Current:** 62 sessions/month at capacity
- **Target:** Handle 80-100 sessions/month comfortably
- **Why:** Accommodate growth without chaos

**Goal 4: Improve Team Efficiency**
- **Current:** Too much time on admin tasks
- **Target:** Reduce admin time by 50%
- **Why:** Focus on core business (photography)

### 3.2 Secondary Goals

- Better client experience (transparency, communication)
- Data-driven decision making (reports, metrics)
- Professional image (moving away from spreadsheets)
- Easier onboarding of new team members
- Historical data for business insights

---

## 4. Users & Stakeholders

### 4.1 User Personas

#### **Persona 1: Maria - Studio Manager**

**Role:** General Manager / Owner  
**Age:** 35  
**Tech Savvy:** Medium  
**Current Pain:** Overwhelmed with coordination tasks, wants to focus on business growth

**Needs:**
- Overview of all operations
- Quick decision-making tools
- Ability to see what's working and what's not
- Manage team members and their permissions

**Goals:**
- Grow the business sustainably
- Maintain service quality
- Keep team happy and productive

**Quote:**
> "I need to see the big picture quickly. Right now, I spend hours every week just trying to understand where we are."

---

#### **Persona 2: Carlos - Coordinator**

**Role:** Session Coordinator (also photographer)  
**Age:** 28  
**Tech Savvy:** Medium-High  
**Current Pain:** Constant back-and-forth with clients, checking availability manually

**Needs:**
- Fast access to availability information
- Easy session creation and management
- Client information at fingertips
- Ability to assign resources quickly

**Goals:**
- Respond to clients faster
- Avoid mistakes in scheduling
- Smooth coordination with photographers and editors

**Quote:**
> "Every time a client asks 'Are you available on X date?', I need to open 3 different files and ask 2 people. It should take 30 seconds, not 30 minutes."

---

#### **Persona 3: Ana - Photographer**

**Role:** Photographer  
**Age:** 26  
**Tech Savvy:** Low-Medium  
**Current Pain:** Doesn't always know her schedule, finds out about changes last minute

**Needs:**
- See her own schedule clearly
- Know details of upcoming sessions
- Update session status after completing work
- Simple interface (not overwhelming)

**Goals:**
- Show up prepared for sessions
- Know what to expect (location, time, client needs)
- Focus on photography, not admin

**Quote:**
> "I just want to know: Where do I need to be, when, and what does the client want? That's it."

---

#### **Persona 4: Luis - Editor**

**Role:** Photo/Video Editor  
**Age:** 24  
**Tech Savvy:** High  
**Current Pain:** Unclear which sessions need editing, no priority system

**Needs:**
- Queue of sessions to edit
- Deadline information
- Ability to update progress
- Manage multiple projects

**Goals:**
- Meet delivery deadlines
- Balanced workload
- Clear expectations from coordinators

**Quote:**
> "Sometimes I have 5 sessions to edit with no idea which is urgent. I need a system that tells me what to work on first."

---

### 4.2 Stakeholders

**Primary Stakeholders:**
- Studio Owner/Manager (Maria)
- Coordinators (Carlos + future hires)
- Photographers (Ana + team)
- Editors (Luis + team)

**Secondary Stakeholders:**
- Clients (end users of photography services)
- Future investors/partners (if business expands)

---

## 5. Core Business Processes

### 5.1 Session Lifecycle (Current Process)

**Phase 1: Initial Contact**
- Client reaches out (phone, email, social media, WhatsApp)
- Wants to know: availability, pricing, services

**Phase 2: Evaluation**
- Coordinator checks if they can serve the client
- Considers:
  - Date and time availability
  - Location (if external)
  - Required photographers/equipment
  - Current workload
- **BOTTLENECK:** This takes too long currently

**Phase 3: Proposal & Negotiation**
- Present package options or custom quote
- Client may request modifications
- Back-and-forth until agreement
- **PAIN POINT:** Sometimes clients walk away during wait

**Phase 4: Confirmation**
- Client agrees to terms
- Must pay 50% deposit
- Have ~5 days to confirm with payment
- If no payment → session is canceled

**Phase 5: Preparation**
- Assign photographers
- Assign studio space (if studio session)
- Prepare equipment
- There's a deadline for changes (~7 days before session)
- After deadline, no major changes allowed

**Phase 6: Execution**
- Photographers attend session
- Capture photos/video
- Session marked as completed

**Phase 7: Editing**
- Editors process the material
- Typically takes 5 days (varies by package)
- Apply corrections, color grading, selection

**Phase 8: Delivery**
- Client is notified material is ready
- Final payment (remaining 50%)
- Deliver digital files and/or prints

**Phase 9: Closed**
- Session complete
- Feedback collected (informal currently)

---

### 5.2 Key Decision Points

**Decision 1: Can we serve this client?**
- **Who decides:** Coordinators (with manager approval for complex cases)
- **Based on:** Availability, capacity, profitability, feasibility
- **Timeline:** Should be within 24 hours (currently takes 2-3 days)

**Decision 2: Pricing for custom requests**
- **Who decides:** Manager or coordinators
- **Based on:** Standard packages + customizations
- **Complexity:** Need to calculate quickly

**Decision 3: Photographer assignment**
- **Who decides:** Coordinators
- **Based on:** Availability, skills, workload balance, location
- **Constraint:** Must not create conflicts

**Decision 4: Accept changes after confirmation**
- **Who decides:** Coordinators/Manager
- **Based on:** How close to session date, nature of changes, impact
- **Policy:** Within 7 days of session → very restricted

---

### 5.3 Client Types

**Type 1: One-Time Event Clients (Most Common)**
- Weddings, birthday parties, quinceañeras
- Single transaction
- High emotional value
- Need: Perfect execution, no room for error

**Type 2: Recurring Institutional Clients**
- Schools (graduation photos)
- Companies (corporate events, headshots)
- Regular business
- Need: Reliability, consistent quality, easy coordination

**Type 3: Individual Personal Clients**
- Portraits, maternity, family photos
- May return for different life events
- Need: Personal attention, creative input

---

## 6. Business Rules & Policies

### 6.1 Pricing & Payments

**Deposit Policy:**
- 50% deposit required to confirm session
- 5 days to make deposit after agreement
- No deposit → session automatically canceled

**Refund Policy:**
- Before confirmation: No payment made, no refund needed
- After confirmation (within change window): 100% refund
- After confirmation (outside change window): 50% refund
- After photographers assigned: No refund (unless studio's fault)
- After session executed: No refund

**Package Structure:**
- Pre-defined packages (most popular option)
- Custom packages (mix and match)
- Add-ons available (extra photos, video, prints, albums)

**Transportation Costs:**
- Included for locations within city
- Remote locations: additional flat fee

---

### 6.2 Session Policies

**Changes Policy:**
- Up to 7 days before session: Changes allowed (may affect price)
- Less than 7 days before: Very limited changes, may require cancellation
- Reason: Need time to coordinate resources

**Cancellation by Client:**
- Before confirmation: Free
- After confirmation (early): Full refund
- After confirmation (late): Partial refund
- After resources assigned: No refund

**Cancellation by Studio:**
- Force majeure (weather, emergency): Full refund
- If studio can't fulfill: Full refund + apology

**Photographer Reassignment:**
- Studio reserves right to reassign photographers if needed
- Client gets notified of changes
- Quality commitment remains the same

---

### 6.3 Service Delivery

**Timeline Commitments:**
- Studio sessions: Ready in 3-7 days (typically 5 days)
- External sessions: Ready in 5-10 days (depends on scope)
- Rush service: Available for additional fee

**Quality Standards:**
- All photos reviewed and edited
- Client receives only best shots (curated)
- Edits include color correction, retouching, cropping

**Delivery Methods:**
- Digital: Cloud link or USB drive
- Physical: Printed photos, albums
- Depends on package selected

---

## 7. Future Vision

### 7.1 Short-Term (Phase 1 - MVP)

**Scope:**
- Core session management
- Basic client database
- Photographer/editor assignment
- Availability checking
- Payment tracking (manual verification)

**Goal:** Solve the critical pain points

---

### 7.2 Medium-Term (Phase 2-3)

**Possible Enhancements:**
- Integrated payment gateway
- Electronic invoicing (legal requirement in Guatemala)
- Client portal (view progress, approve photos)
- Mobile app for photographers
- Advanced reporting and analytics
- Automated reminders and notifications (SMS)

---

### 7.3 Long-Term Vision

**Dream Features:**
- AI-assisted photo selection
- Online booking for clients (self-service)
- Integration with social media
- Marketing automation
- Equipment management
- Multiple studio locations
- Franchise expansion support

---

## Constraints & Considerations

- Phased development approach
- MVP approach: solve critical needs first

---

**End of Document**

*For technical implementation details, see:*
- `database-schema.sql` - Data model
- `business-rules.md` - Technical rules and validations
- `permissions.md` - Access control matrix