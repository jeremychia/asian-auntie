# Legal Compliance Implementation Checklist

Quick reference checklist for implementing legal compliance across all features and jurisdictions.

---

## Phase 1: Critical (First 4 Weeks)

### Privacy & Data Protection

- [ ] **Create Privacy Policy**

  - [ ] Include sections for each feature (Manage, Recipes, Trade)
  - [ ] Specify data collected, purposes, legal basis
  - [ ] Include retention periods
  - [ ] List third-party processors
  - [ ] Translations: French, German, English (base language)

- [ ] **Implement Consent Management**

  - [ ] Explicit opt-in for data collection (non-pre-checked boxes)
  - [ ] Separate consents: Analytics, Marketing, Core functionality
  - [ ] Show consent statements at signup and before data collection
  - [ ] Ability to withdraw consent easily (Settings → Privacy)
  - [ ] Log consent timestamps and version accepted

- [ ] **Add Disclaimers** (visible to all users)
  - [ ] **Manage Perishables**: "For inventory tracking only. Always verify expiry dates."
  - [ ] **Recipes**: "Recipes for informational use. Verify ingredients and cooking techniques."
  - [ ] **Trade**: "Food safety is YOUR responsibility. Trade non-perishable items. Follow food safety laws."

### Terms of Service

- [ ] **Create ToS for Trade Perishables** (highest priority)

  - [ ] Liability limits: "Platform is not liable for food quality or safety"
  - [ ] User responsibility: "Users responsible for food safety compliance"
  - [ ] Prohibited items list
  - [ ] Indemnification clause
  - [ ] Dispute resolution process
  - [ ] Acceptance required before trading

- [ ] **Create General ToS** (if not already existing)
  - [ ] Account creation and usage terms
  - [ ] Intellectual property rights
  - [ ] Limitation of liability
  - [ ] Dispute resolution/arbitration

### Location-Specific Requirements

- [ ] **Germany: Impressum (Legal Notice)**

  - [ ] Create /impressum page with:
    - [ ] Business name/person name
    - [ ] Full postal address
    - [ ] Email and phone
    - [ ] VAT ID (if applicable)
    - [ ] Handelsregister info (if applicable)
  - [ ] Link from footer on all pages
  - [ ] Update annually

- [ ] **France: CNIL Notification**
  - [ ] Register with CNIL if processing personal data at scale
  - [ ] Include CNIL contact in privacy policy
  - [ ] Document lawful basis for processing

---

## Phase 2: Important (Weeks 2-4)

### Data Handling

- [ ] **Implement Data Deletion**

  - [ ] Delete account and associated data within 30 days of request
  - [ ] Delete transaction/contact data 30 days after trade completion
  - [ ] Retain minimal logs for legal compliance only
  - [ ] Document retention rationale

- [ ] **Encrypt Sensitive Data**

  - [ ] SSL/TLS for all data in transit (HTTPS everywhere)
  - [ ] Encrypt passwords (bcrypt/Argon2)
  - [ ] Encrypt messaging data at rest (if applicable)
  - [ ] Document encryption methods

- [ ] **Implement Data Subject Rights Portal**
  - [ ] Access: Download data in machine-readable format (JSON/CSV)
  - [ ] Correction: Update personal information
  - [ ] Erasure: Delete account and data (with exceptions documented)
  - [ ] Portability: Export data to another service
  - [ ] Opt-out: Disable analytics/marketing/profiling

### Food Safety & Content Moderation

- [ ] **Recipe Attribution**

  - [ ] Audit all recipes: Document source and copyright status
  - [ ] Obtain licenses for copyrighted recipes (email creators, use CC-licenses)
  - [ ] Add source attribution and license info to each recipe
  - [ ] Document copyright compliance spreadsheet

- [ ] **Content Moderation for Trade**

  - [ ] Create reporting mechanism (flag/report button)
  - [ ] SLA: Respond to safety reports within 24-48 hours
  - [ ] Remove suspicious trades (spoiled food, no allergen info, expired items)
  - [ ] Maintain moderation log (date, action, reason)
  - [ ] Option to appeal removal decisions

- [ ] **Add Food Safety Guidance**
  - [ ] Link to official food safety authorities per jurisdiction:
    - [ ] US: FDA (fda.gov) — Food Safety Modernization Act (FSMA) guidance
    - [ ] Canada: Health Canada + CFIA (inspection.canada.ca) — Safe Food for Canadians Act (SFCA)
    - [ ] UK: FSA — Food Standards Agency (food.gov.uk) — Food Safety Act 1990 + Food Information Regulations 2014
    - [ ] Singapore: SFA — Singapore Food Agency (sfa.gov.sg) — Sale of Food Act (Cap. 283); **not NEA/EPHA** (SFA took over food safety in 2019)
    - [ ] France/Germany: EFSA (efsa.europa.eu) + national authorities (ANSES for France, BfR for Germany)
  - [ ] Recommend non-perishable items for trading
  - [ ] **Allergen disclosure: enforce as platform requirement** (not just education) — backed by law in every jurisdiction:
    - [ ] EU (France/Germany): EU Regulation 1169/2011 — 14 allergens mandatory
    - [ ] UK: Food Information Regulations 2014 (SI 2014/1855) — 14 allergens mandatory
    - [ ] Singapore: Food Regulations (Cap. 283, Rg 1) — allergen disclosure required
    - [ ] US: FALCPA (21 U.S.C. §343(w)) — 9 major allergens mandatory
    - [ ] Canada: SFCR Schedule 9 (SOR/2018-108) — 14 priority allergens mandatory
  - [ ] Document food safety standards per jurisdiction

### Jurisdiction-Specific

- [ ] **Canada: CASL Compliance**

  - [ ] For any email/SMS marketing or notifications:
    - [ ] Explicit opt-in consent (non-pre-checked)
    - [ ] Clear sender identification
    - [ ] Easy unsubscribe link/address
    - [ ] Include mailing address
    - [ ] Honor unsubscribe within 10 business days
  - [ ] Translations: English and French

- [ ] **UK: Marketing Compliance (PECR)**
  - [ ] For marketing emails: Obtain explicit prior consent
  - [ ] Include unsubscribe link in every email
  - [ ] Do not use soft opt-in

---

## Phase 3: Extended (Months 2-3)

### Documentation & Compliance

- [ ] **Create Data Processing Documentation**

  - [ ] Data mapping: What data, from where, to where, why?
  - [ ] DPIA (Data Protection Impact Assessment) if profiling/analytics
  - [ ] Third-party processor agreements (if using cloud, analytics, etc.)
  - [ ] Data retention schedule
  - [ ] Breach notification procedure (if personal data is breached)

- [ ] **Implement Audit Logging**

  - [ ] Log admin actions (data access, deletions, user suspensions)
  - [ ] Log security events (failed logins, permission changes)
  - [ ] Retention: Audit logs for 12 months minimum
  - [ ] Non-tamper mechanism (immutable logs)

- [ ] **Create Privacy Officer Contact**
  - [ ] Designate privacy contact email (privacy@[domain])
  - [ ] Respond to data subject requests within 30 days
  - [ ] Document request handling process

### Recipe Feature Compliance

- [ ] **Allergen Accuracy in Recipes** (legal obligation, not just UX)

  - [ ] If displaying allergen tags on recipes, verify accuracy against the recipe source
  - [ ] Do not auto-generate allergen labels from LLM output without verification — inaccurate allergen info creates liability under FALCPA (US), FIR 2014 (UK), EU 1169/2011 (France/Germany), and equivalents
  - [ ] Add disclaimer: "Always verify allergens with original recipe source. Allergen information may not be complete."
  - [ ] Consider flagging recipes where allergen data is unverified

- [ ] **Copyright Licensing Spreadsheet**

  - [ ] Recipe name, source, copyright holder, license type, license link, date obtained
  - [ ] For each recipe, mark as: Licensed, CC-Licensed, Fair Use (US), Public Domain, or Original
  - [ ] Fair Use recipes: Document Fair Use analysis (transformation, education, minimal copying)

- [ ] **Recipe Attribution Page**
  - [ ] List all sources with links
  - [ ] Include license types
  - [ ] Thank original creators
  - [ ] Link to original recipes/sources

### Consumer Rights Implementation

- [ ] **Create User Request Form**
  - [ ] SAR (Subject Access Request) - GDPR, UK-GDPR, PDPA
  - [ ] Deletion request - GDPR, US (CCPA)
  - [ ] Correction request - GDPR, PDPA
  - [ ] Opt-out - CCPA (US)
  - [ ] Process requests within 30 days

---

## Phase 4: Ongoing (Months 3+)

### Regular Reviews

- [ ] **Quarterly Compliance Review**

  - [ ] Update privacy policy based on new regulations
  - [ ] Review moderation logs for patterns/issues
  - [ ] Audit third-party processor compliance
  - [ ] Check for new state/country-specific laws
  - [ ] Schedule: April, July, October, January

- [ ] **Annual Legal Review**
  - [ ] Consult local lawyers in each jurisdiction
  - [ ] Update ToS based on case law/regulatory changes
  - [ ] Verify Impressum is current (Germany)
  - [ ] Review food safety standards updates
  - [ ] Schedule: Q1 of each year

### Monitoring & Updates

- [ ] **Regulatory Tracking**

  - [ ] Subscribe to regulatory updates (CNIL, ICO, PDPC, etc.)
  - [ ] Monitor EU Digital Services Act (DSA) updates if operating in EU
  - [ ] Track state-level privacy law changes (US)
  - [ ] Follow AI regulation developments

- [ ] **Incident Response**
  - [ ] Develop data breach response plan (notification within 72 hours in GDPR)
  - [ ] Document incident response procedures
  - [ ] Test breach notification process annually

---

## Jurisdiction-Specific Priority Order

### If launching in France first:

1. GDPR Privacy Policy (French)
2. Consent management
3. CNIL registration (if processing data at scale)
4. Data deletion mechanism
5. Trade ToS with food safety disclaimer

### If launching in Germany first:

1. Impressum (legal notice)
2. Privacy Policy (German)
3. GDPR consent management
4. DPA with third-party processors
5. Encryption
6. Trade ToS with LFGB food safety

### If launching in UK first:

1. Privacy Notice (UK-GDPR compliant)
2. Consumer Rights notices
3. PECR compliance (marketing)
4. Data deletion mechanism
5. Trade ToS with Food Safety Act 1990 + Food Information Regulations 2014 disclaimers
6. Allergen disclosure enforcement (FIR 2014 — 14 allergens mandatory in Trade and Recipes)

### If launching in Singapore first:

1. Privacy Policy (PDPA-compliant)
2. Consent (deemed consent acceptable for non-sensitive data)
3. Cross-border data transfer assessment
4. Data subject rights (access, correction)
5. Trade ToS with Sale of Food Act (Cap. 283) + SFA Act 2019 food safety requirements
6. Allergen disclosure enforcement (Food Regulations Cap. 283, Rg 1)
   Note: Reference SFA (Singapore Food Agency) as the regulator — not NEA/EPHA for food safety

### If launching in US first:

1. Privacy Policy (CCPA if California users)
2. Consumer rights (access, delete, opt-out)
3. Food safety disclaimers aligned with FSMA (21 U.S.C. §2201)
4. Allergen disclosure enforcement (FALCPA, 21 U.S.C. §343(w)) — 9 major allergens in Trade and Recipes
5. Recipe copyright licenses/attribution
6. Trade ToS with liability disclaimers + note on state cottage food law exemptions

### If launching in Canada first:

1. Privacy Policy (English and French for Quebec)
2. CASL compliance (marketing emails/SMS)
3. PIPEDA consent (explicit, non-pre-checked boxes)
4. Safe Food for Canadians Act (SFCA) + SFCR compliance (replaces Food and Drugs Act for food safety)
5. Allergen disclosure enforcement (SFCR Schedule 9 — 14 priority allergens mandatory)
6. Trade ToS with food safety disclaimers in English and French

---

## Testing Checklist

Before each launch in a new jurisdiction:

### Privacy & Consent

- [ ] Signup flow: Consent checkboxes are NOT pre-checked
- [ ] Consent text is clear and easy to understand
- [ ] Users can withdraw consent (Settings → Privacy)
- [ ] Deletion request within 30 days
- [ ] Data export in machine-readable format (JSON/CSV)

### Trade Feature

- [ ] Liability disclaimer visible before first trade
- [ ] Prohibited items list is clear
- [ ] Users required to accept ToS before trading
- [ ] Report/flag button is visible
- [ ] Moderation queue reviewed daily

### Recipe Feature

- [ ] Each recipe displays source attribution
- [ ] License information is visible
- [ ] Link to original source works
- [ ] No deceptive claims ("authentic," "traditional" qualified)
- [ ] Allergen information is verified (not LLM-generated without checking) — legal obligation in all jurisdictions
- [ ] Disclaimer visible: "Always verify allergens with original source"

### Trade Feature — Allergen Enforcement

- [ ] Sellers are required to disclose allergens before listing (enforce in UI, not just ToS)
- [ ] Listings without allergen disclosure are blocked or flagged
- [ ] Allergen disclaimer visible on every listing page

### Location-Specific

- [ ] **Germany**: Impressum page complete and linked; EU Reg 1169/2011 allergen requirements met
- [ ] **France**: Privacy Policy in French; EU Reg 1169/2011 allergen requirements met
- [ ] **Canada**: Privacy Policy in French (for Quebec market); SFCR Schedule 9 allergens disclosed
- [ ] **Singapore**: Food safety guidelines linked to SFA (sfa.gov.sg) — not NEA
- [ ] **US**: FDA guidance linked; FALCPA 9 allergens disclosed in Trade and Recipes
- [ ] **UK**: Food Information Regulations 2014 allergen requirements met; FSA guidance linked

---

## Risk Assessment Template

After implementing each jurisdiction, assess residual risk:

| Requirement                             | Status     | Risk Level            | Notes |
| --------------------------------------- | ---------- | --------------------- | ----- |
| Privacy Policy (jurisdiction-specific)  | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Consent Management                      | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Trade ToS & Liability                   | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Food Safety Disclaimers                 | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Recipe Attribution/Licensing            | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Data Deletion/Retention                 | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Encryption & Security                   | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Content Moderation                      | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |
| Jurisdiction-Specific (Impressum, etc.) | ☐ Complete | ☐ Low ☐ Medium ☐ High |       |

---

## Document References

- **Detailed Legal Analysis**: `LEGAL-RISKS.md` (this folder)
- **Privacy Policy Template**: Generate with Privacy Policy generator or hire lawyer
- **ToS Template**: Customizable based on LEGAL-RISKS.md requirements
- **Moderation Policy**: Based on content moderation section in LEGAL-RISKS.md

---

**Last Updated**: April 2026
**Next Review**: July 2026
