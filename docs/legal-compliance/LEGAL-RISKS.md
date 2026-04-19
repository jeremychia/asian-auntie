# Legal Compliance & Risk Assessment

**Date**: April 2026
**Scope**: Legal risks for Asian Auntie features across 6 countries

---

## Overview

Asian Auntie implements three core features:

1. **Manage Perishables**: Track expiry dates of food items, quantity, purchase history
2. **Recommend Recipes**: Provide recipe suggestions based on available ingredients
3. **Trade Perishables**: Peer-to-peer marketplace for sharing/trading excess ingredients

This document identifies legal risks and required compliance actions for each feature in: France, Germany, United Kingdom, Singapore, United States, and Canada.

---

## 1. MANAGE PERISHABLES

### 1.1 France

#### Applicable Laws

- **CNIL (Commission Nationale de l'Informatique et des Libertés)** regulations under **French Data Protection Act (Loi Informatique et Libertés)**
- **GDPR** (EU General Data Protection Regulation 2016/679) - applies to all EU member states

#### Legal Risks

| Risk                                     | Description                                                                                                                                            | Jurisdiction                                 |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| **Data storage of personal information** | Storing purchase dates, item quantities, and expiry information constitutes personal data                                                              | GDPR Article 4                               |
| **Lack of legal basis**                  | Must have explicit lawful basis (consent, contract, legal obligation, vital interests, public task, legitimate interests) for processing personal data | GDPR Article 6                               |
| **Profiling from purchase history**      | Analyzing buying patterns and waste patterns could constitute automated profiling                                                                      | GDPR Article 22                              |
| **Cookies/tracking without consent**     | Analytics or tracking pixels require explicit prior consent (cookie banner)                                                                            | French Directive 2002/58/EC, CNIL Guidelines |

#### Required Actions

✅ **Implement GDPR compliance**:

- [ ] Create a privacy policy in French (mandatory for French users) and English
- [ ] Obtain explicit opt-in consent for personal data collection (not pre-checked boxes)
- [ ] Include legal basis statement: e.g., "We process your data based on your consent to provide this service"
- [ ] Implement right-to-access, right-to-erasure ("droit à l'oubli"), data portability
- [ ] Conduct a Data Protection Impact Assessment (DPIA) if profiling/analytics are implemented
- [ ] Set data retention policy (e.g., "We delete purchase history after 12 months of account inactivity")
- [ ] Register with CNIL if processing personal data at scale

✅ **Cookie compliance**:

- [ ] Add cookie banner asking for explicit consent _before_ any tracking
- [ ] Separate consent for analytics, functional cookies, and marketing cookies
- [ ] Document cookie usage in privacy policy

✅ **Contact Information**:

- [ ] Publish a Data Protection Officer (DPO) contact or privacy contact email

---

### 1.2 Germany

#### Applicable Laws

- **GDPR** (Regulation 2016/679)
- **Bundesdatenschutzgesetz (BDSG)** - German Data Protection Act (complementary to GDPR)
- **Telemediengesetz (TMG)** - Telemedia Act (German law for online services)
- **Impressum requirement** (TMG §7)
- **LFGB (Lebensmittel- und Futtermittelgesetzbuch)** - German Food and Feed Code: if the app surfaces food safety guidance (e.g., "item has expired — discard"), it becomes a communication of food safety information and falls within LFGB scope
- **BfR (Bundesinstitut für Risikobewertung)** guidelines - Federal Institute for Risk Assessment: authoritative source for food safety claims in Germany

#### Legal Risks

| Risk                  | Description                                                                    | Jurisdiction |
| --------------------- | ------------------------------------------------------------------------------ | ------------ |
| **Missing Impressum** | All online services must provide legal/business information                    | TMG §7       |
| **GDPR violations**   | Personal data processing without explicit consent                              | GDPR         |
| **Age verification**  | No clear mechanism to prevent minors from accessing if handling sensitive data | TMG §7, GDPR |

#### Required Actions

✅ **Implement Impressum (legal notice)**:

- [ ] Create an "Impressum" page (German requirement, not optional)
- [ ] Include:
  - Name of service provider (individual or company name)
  - Full postal address
  - Email address or contact form
  - Phone number
  - Value Added Tax (VAT) ID if applicable
  - Business registration (Handelsregister) if applicable
  - Responsible editor/person (for editorial content)

✅ **GDPR compliance** (same as France, plus):

- [ ] Privacy Policy must be in German
- [ ] Implement DPA (Data Processing Agreement) if using third-party processors (e.g., cloud providers, analytics)
- [ ] Must be able to prove lawful basis for data processing

✅ **User data safety**:

- [ ] Implement encryption for data at rest and in transit (SSL/TLS)
- [ ] Document data security measures in privacy policy

**Example Impressum Structure**:

```
Betreiber und Verantwortlicher:
[Name]
[Street Address]
[Postal Code and City]
[Country]

Kontakt:
E-Mail: [email]
Telefon: [phone]

USt-IdNr: [VAT ID if applicable]
Handelsregister: [Registration if applicable]
```

---

### 1.3 United Kingdom

#### Applicable Laws

- **GDPR** (still applies post-Brexit under UK-GDPR)
- **Data Protection Act 2018**
- **Privacy and Electronic Communications Regulations 2003 (PECR)**
- **Information Commissioner's Office (ICO)** guidance
- **Food Safety Act 1990** - if the app surfaces food safety guidance (e.g., expiry alerts or disposal recommendations), it may constitute a food safety communication under this Act

#### Legal Risks

| Risk                                      | Description                                                                                                                           | Jurisdiction           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| **No lawful basis for data processing**   | Must document why you process personal data (consent, contract, legal obligation, vital interests, public task, legitimate interests) | UK-GDPR Article 6      |
| **Marketing emails without consent**      | Sending marketing emails to individuals requires prior explicit consent under PECR                                                    | PECR Regulation 22     |
| **Inadequate transparency**               | Users must know exactly what data is collected and why                                                                                | UK-GDPR Articles 13-14 |
| **No data subject rights implementation** | Users have right to access, rectify, erase, restrict processing, data portability                                                     | UK-GDPR Chapter 3      |

#### Required Actions

✅ **UK-GDPR compliance**:

- [ ] Privacy Notice: Provide clear, accessible privacy information _at point of collection_
- [ ] Lawful Basis: Document and display which lawful basis applies (e.g., "You have consented to data processing")
- [ ] Data Subject Rights: Implement mechanisms to:
  - Request data access (SAR - Subject Access Request)
  - Request data erasure ("right to be forgotten")
  - Request data portability (in structured, machine-readable format)
  - Withdraw consent at any time
- [ ] Document retention policy (e.g., "We retain purchase history for 12 months after last account activity")

✅ **PECR compliance** (for marketing):

- [ ] If planning to send marketing emails/SMS: Obtain explicit opt-in consent first
- [ ] Include unsubscribe link in every marketing message
- [ ] Do not use soft opt-in (pre-checked boxes) for marketing consent

✅ **Contact with ICO**:

- [ ] Consider registering with ICO if processing personal data
- [ ] Display privacy contact email clearly

---

### 1.4 Singapore

#### Applicable Laws

- **Personal Data Protection Act (PDPA)** - Singapore's primary data protection statute
- **PDPA Schedule 2** - Deemed consent opt-out model (differs from GDPR's opt-in)
- **Sale of Food Act (Cap. 283)** + **Singapore Food Agency (SFA) Act 2019** - if the app surfaces expiry or food safety guidance, this framework may apply

#### Legal Risks

| Risk                                         | Description                                                                                                         | Jurisdiction                 |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **Collecting personal data without consent** | PDPA requires consent, but allows "deemed consent" for direct marketing                                             | PDPA Section 14              |
| **No Privacy Policy**                        | Must provide clear, understandable collection statement at or before collection                                     | PDPA Schedule 2, Paragraph 1 |
| **International data transfer**              | Personal data of Singapore residents cannot be transferred to countries without "adequate personal data protection" | PDPA Section 26              |
| **No data subject rights**                   | Users have rights to access, correct, and request erasure of personal data                                          | PDPA Sections 19-21          |

#### Required Actions

✅ **PDPA compliance**:

- [ ] Create Privacy Policy (required by law)
- [ ] Obtain consent for personal data collection:
  - Affirmative consent for sensitive purposes (health, financial, government ID)
  - Deemed consent acceptable for non-sensitive purposes (e.g., purchase history)
  - Must still provide clear notification
- [ ] Consent can be withdrawn at any time
- [ ] Collect personal data only for legitimate purposes and disclose purpose clearly

✅ **Data Subject Rights**:

- [ ] Implement mechanism for users to:
  - Access their personal data (free first request, nominal fee for subsequent)
  - Correct inaccurate data
  - Request erasure (where reasonably possible)
  - Withdraw consent

✅ **Cross-border data transfer**:

- [ ] If user data is stored or transferred outside Singapore:
  - Conduct adequacy assessment: Does destination country have adequate data protection?
  - France, Germany, UK, US: Adequate protections
  - Canada: Adequate protections
  - If not adequate, implement contractual safeguards (Standard Contractual Clauses, Binding Corporate Rules)
  - Document transfer arrangements

✅ **Personal Data Protection Officer**:

- [ ] Designate or notify PDPC of data protection officer contact details
- [ ] Publish contact for data subject inquiries

---

### 1.5 United States

#### Applicable Laws

- **No federal omnibus data protection law** (unlike GDPR)
- **State-level laws** (California, Virginia, Colorado, Connecticut, Utah, Montana, Delaware, Indiana, Missouri):
  - **California Consumer Privacy Act (CCPA)** / **California Privacy Rights Act (CPRA)**
  - **Virginia Consumer Data Protection Act (VCDPA)**
  - **Colorado Privacy Act (CPA)**
  - **Other state laws** (emerging)
- **FTC Act Section 5** - Prohibits unfair/deceptive practices in data handling
- **Food Safety Modernization Act (FSMA, 21 U.S.C. §2201)** - if the app surfaces food safety advice (expiry alerts, storage guidance), claims must align with FDA food safety standards
- **State-specific health/food laws** for food safety claims

#### Legal Risks

| Risk                                          | Description                                                                                    | Jurisdiction                |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------- |
| **CCPA/CPRA violations (California)**         | If users are in California: collect personal information but fail to implement consumer rights | CCPA §1798.100 et seq.      |
| **Deceptive privacy practices**               | Claiming privacy protections but not implementing them                                         | FTC Act §5                  |
| **Food safety claims without substantiation** | If implying app helps with food safety, could be deceptive                                     | FTC Act §5, FDA regulations |
| **No consumer rights (non-CCPA states)**      | Outside CCPA/CPRA/similar states, no legal requirement for consumer rights, but best practice  | N/A                         |

#### Required Actions

✅ **If operating in California or other CCPA-equivalent states**:

- [ ] Create Privacy Policy disclosing:
  - Categories of personal information collected
  - Source of personal information
  - Business purpose of collection
  - Categories of third parties with whom data is shared
  - Consumer rights available
- [ ] Implement CCPA Consumer Rights:
  - Right to access ("Know what personal information is collected")
  - Right to delete (with narrow exceptions)
  - Right to correct inaccurate data
  - Right to opt-out of "sale" or "sharing" (if applicable)
  - Right to non-discrimination if exercising CCPA rights
- [ ] Honor do-not-sell/do-not-share requests
- [ ] Create mechanism for users to verify identity (for access/delete requests)
- [ ] Disclose financial incentives if offering opt-in rewards

✅ **If operating nationally (recommended best practice)**:

- [ ] Treat all users as if under CCPA to minimize compliance burden:
  - Universal privacy policy
  - Offer consumer rights to all users
  - Simple opt-out mechanisms
- [ ] FTC Compliance:
  - Don't make deceptive claims about food safety
  - If claiming app "prevents food waste," substantiate claim with evidence
  - Document data security practices

✅ **Food Safety Claims**:

- [ ] If marketing app as helping with food safety (expiry dates), ensure claims are:
  - Truthful and substantiated
  - Not misleading about what app actually does
  - Compliant with FDA guidelines on food handling
- [ ] Disclaimer: "This app is for personal inventory tracking only. Always follow FDA food safety guidelines."

---

### 1.6 Canada

#### Applicable Laws

- **Personal Information Protection and Electronic Documents Act (PIPEDA)** - Federal privacy law
- **Quebec Law 25 (Bill 64)** - Modernized Quebec privacy law (coming into force gradually, some provisions effective 2024+)
- **Provincial privacy laws** (Alberta, BC: also have PIPEDA-like laws)
- **CASL (Canada's Anti-Spam Legislation)** - Applies to all electronic messages
- **Safe Food for Canadians Act (SFCA, S.C. 2012, c. 24)** - if app surfaces expiry or food safety guidance, claims must be consistent with SFCA/SFCR standards

#### Legal Risks

| Risk                               | Description                                                                      | Jurisdiction              |
| ---------------------------------- | -------------------------------------------------------------------------------- | ------------------------- |
| **PIPEDA violations**              | Collecting personal data without meaningful consent (not just pre-checked boxes) | PIPEDA Part 2, Schedule 1 |
| **No Privacy Policy**              | Must provide clear notice of practices at or before collection                   | PIPEDA Section 4.2        |
| **Unsolicited marketing messages** | Sending marketing emails/texts without prior express consent illegal             | CASL Section 6(1)         |
| **Quebec Law 25 compliance**       | Quebec has stricter requirements than PIPEDA (consent-focused, expanded rights)  | Quebec Law 25             |

#### Required Actions

✅ **PIPEDA/Quebec Law 25 compliance**:

- [ ] Create Privacy Policy in both English and French (mandatory for Quebec market)
  - Quebec Law 25 requires French as co-official language
- [ ] Obtain meaningful consent:
  - Not pre-checked boxes ("meaningful" per PIPEDA jurisprudence)
  - Clear statement: "By clicking agree, you consent to collection of [specific data] for [specific purposes]"
  - Separate consent for marketing if applicable
- [ ] Implement data subject rights:
  - Access to personal information (within 30 days, subject to exemptions)
  - Correction of inaccurate information
  - Request deletion (where reasonably possible)
- [ ] Document retention policy
- [ ] Appoint Privacy Officer contact and publish details

✅ **CASL compliance** (critical):

- [ ] For marketing emails/SMS:
  - [ ] Obtain **express** prior consent (opt-in, not soft opt-in)
  - [ ] Consent must be affirmative (checked boxes, explicit agreement)
  - [ ] Include in every message:
    - Clear identification of sender
    - Easy-to-use unsubscribe mechanism (email address or link)
    - Physical mailing address of sender
  - [ ] Honor unsubscribe requests within 10 business days
- [ ] Penalties for CASL violations: $1 million CAD (individual), $15 million CAD (corporation) per violation
- [ ] Do NOT use pre-checked boxes for marketing consent (violates CASL)

✅ **Quebec-specific requirements (Law 25)**:

- [ ] Privacy Policy in French and English
- [ ] Stricter consent requirements than PIPEDA (more explicit)
- [ ] Right to request explanation of decisions based on automated profiling
- [ ] Expanded data portability requirements

---

## 2. RECOMMEND RECIPES

### 2.1 France

#### Applicable Laws

- **GDPR** (ingredient matching is personal data processing)
- **French Law on Freedom of Communication (Loi Liberté de Communication)** - content responsibility
- **French Copyright Law (Code de la Propriété Intellectuelle)** - recipe sourcing/attribution
- **EU Regulation (EU) No 1169/2011** - Food Information to Consumers (FIC): mandates allergen labeling in food communications; if recipes display allergen info, this regulation applies

#### Legal Risks

| Risk                                     | Description                                                                                     | Jurisdiction                           |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------- |
| **Processing ingredient preferences**    | Storing and analyzing ingredient preferences constitutes personal data                          | GDPR Article 4                         |
| **Recipe copyright infringement**        | Reproducing recipe text/images without license                                                  | French Copyright Law, GDPR-adjacent    |
| **Missing attribution**                  | If sourcing recipes from third parties, must credit source                                      | French Copyright Law, Berne Convention |
| **LLM-generated content responsibility** | If using LLM to generate recommendations, app is responsible for accuracy/legality              | French Law on Freedom of Communication |
| **Accessibility requirement**            | RGAA (General Reference Accessibility Rules) requires digital accessibility for public services | RGAA 4.1                               |

#### Required Actions

✅ **GDPR compliance** (same as Manage Perishables):

- [ ] Privacy policy explaining ingredient preference collection
- [ ] Obtain consent for profiling based on ingredient data
- [ ] Implement DPIA for automated recipe recommendation system

✅ **Recipe sourcing and copyright**:

- [ ] If sourcing recipes from external sources:
  - [ ] Obtain explicit license to reproduce (contact recipe creator/publisher)
  - [ ] Always attribute source (e.g., "Recipe from [Name] via [Source]")
  - [ ] Document license agreements (CC-BY, CC-BY-SA, Fair Use, custom)
- [ ] If generating recipe variations via LLM:
  - [ ] Use original recipes only as reference (adapt/transform significantly)
  - [ ] Credit original source when appropriate
  - [ ] Add disclaimer: "AI-assisted variation. Original source: [...]"
- [ ] If aggregating recipes (recipe database):
  - [ ] Obtain permission from each source or use CC-licensed recipes
  - [ ] Maintain license attribution metadata

✅ **Content responsibility**:

- [ ] Disclaimer: "Recipes are for informational purposes. Follow standard food safety practices."
- [ ] Don't make health claims without substantiation (e.g., "This recipe is gluten-free" is fact, "cures allergies" is not)
- [ ] Implement user reporting mechanism for flagging illegal/harmful content

---

### 2.2 Germany

#### Applicable Laws

- **GDPR** (profiling for recipe recommendations)
- **TMG** (Impressum still required)
- **German Copyright Law (Urheberrechtsgesetz)** - recipe copyright protection
- **AStA-Urteil** (Bundesgerichtshof) - landmark ruling on recipe copyright
- **EU Regulation (EU) No 1169/2011** - Food Information to Consumers (FIC): if the app displays allergen information in recipes, this directly applies; allergen data must be accurate and complete

#### Legal Risks

| Risk                                     | Description                                                                       | Jurisdiction                                    |
| ---------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Recipe copyright**                     | Recipes can be copyrighted if they express creativity (not just ingredient lists) | German Copyright Law §2, BGH Urteil I ZR 112/86 |
| **No Impressum**                         | Still required even with recommendation feature                                   | TMG §7                                          |
| **Ingredient profiling without consent** | Systematic profiling of cooking preferences requires explicit GDPR consent        | GDPR Article 6, 9                               |
| **AI accountability**                    | If using LLM for recommendations, must disclose AI involvement                    | German AI Act (awaiting final provisions)       |

#### Required Actions

✅ **Recipe copyright protection**:

- [ ] Audit all recipes in database:
  - [ ] Obtain explicit licenses from copyright holders (email recipe creators, publishers)
  - [ ] Use only CC-licensed recipes (CC0, CC-BY, CC-BY-SA) if not obtaining licenses
  - [ ] Ingredient lists alone are not copyrightable (may use freely)
  - [ ] Recipe instructions, presentation, creative elements are copyrightable
- [ ] For each recipe, store and display:
  - [ ] Source/attribution
  - [ ] License type
  - [ ] Date obtained
- [ ] Create "Attribution" page linking to all original sources

✅ **AI transparency** (future compliance):

- [ ] If using AI to generate recommendations:
  - [ ] Disclose in privacy policy: "We use machine learning to recommend recipes"
  - [ ] Allow users to opt-out of AI-based recommendations
  - [ ] Document how AI decisions are made (transparency)

✅ **Impressum** (same as above):

- [ ] Include on every page

---

### 2.3 United Kingdom

#### Applicable Laws

- **UK-GDPR** (ingredient profiling)
- **Copyright, Designs and Patents Act 1988** - recipe copyright
- **Consumer Rights Act 2015** - recipe accuracy/misleading claims
- **Advertising Standards Authority (ASA)** - recipe claims
- **Food Information Regulations 2014 (SI 2014/1855)** - UK post-Brexit equivalent of EU 1169/2011; if the app displays allergen information in recipes, it must be accurate and complete; 14 major allergens must be clearly highlighted

#### Legal Risks

| Risk                              | Description                                                             | Jurisdiction                |
| --------------------------------- | ----------------------------------------------------------------------- | --------------------------- |
| **Recipe copyright infringement** | Recipes with creative expression are copyright-protected                | CDPA 1988 §1                |
| **No source attribution**         | Moral right to attribution (reputation)                                 | CDPA 1988 §77               |
| **Misleading recipe claims**      | "Authentic," "traditional," "approved by chef" without substantiation   | Consumer Rights Act 2015 §5 |
| **Ingredient accuracy**           | If recommending recipes based on user ingredients, must ensure accuracy | Consumer Rights Act 2015    |

#### Required Actions

✅ **Recipe sourcing and copyright**:

- [ ] Obtain licenses for all recipes:
  - [ ] Contact recipe creators/publishers directly for permission
  - [ ] Use only CC-licensed recipes
  - [ ] Maintain license documentation
- [ ] Always attribute:
  - [ ] Display author name, recipe source, and original publication
  - [ ] Link to original source where possible
- [ ] Copyright notice: "Recipe © [Year] [Author/Publisher]. Used with permission."

✅ **Claims substantiation**:

- [ ] Never claim recipe is "authentic" unless:
  - [ ] Attributed to a recognized source (cookbook, chef, cultural authority)
  - [ ] Recipe creator confirms authenticity
- [ ] Avoid claims like:
  - ❌ "Approved by celebrity chef" (without actual approval)
  - ❌ "Traditional Asian recipe" (without cultural verification)
  - ✅ "Traditional recipe as prepared in [region] per [source]"
- [ ] Include disclaimer: "Recipe recommendations are informational only."

---

### 2.4 Singapore

#### Applicable Laws

- **PDPA** (ingredient profiling)
- **Copyright Act** - recipe copyright protection
- **Consumer Protection (Fair Trading) Act (CPFTA)** - misleading claims
- **Food Regulations (Cap. 283, Rg 1)** under the Sale of Food Act - specifies allergen and labeling standards; if the app displays allergen or nutritional information in recipes, it must meet these standards

#### Legal Risks

| Risk                          | Description                                                                 | Jurisdiction                    |
| ----------------------------- | --------------------------------------------------------------------------- | ------------------------------- |
| **Ingredient data profiling** | Tracking ingredient preferences and making inferences requires PDPA consent | PDPA Section 14                 |
| **Recipe copyright**          | Recipes with original expression are copyright-protected                    | Copyright Act §2, 31            |
| **Misleading claims**         | Claiming recipes are "authentic" or "chef-approved" without substantiation  | CPFTA Part II                   |
| **No source attribution**     | Failure to credit original recipe creator                                   | Copyright Act, Moral Rights §82 |

#### Required Actions

✅ **PDPA compliance** (ingredient profiling):

- [ ] Obtain consent for:
  - [ ] Collection of ingredient preferences
  - [ ] Analysis/profiling of cooking patterns
  - [ ] Use of profiling for recipe recommendations
- [ ] Provide notice: "We collect ingredient preferences to recommend recipes tailored to you"
- [ ] Implement opt-out mechanism

✅ **Recipe copyright**:

- [ ] Obtain licenses for all recipes
- [ ] Always credit original source with:
  - [ ] Recipe creator name
  - [ ] Original publication/website
  - [ ] License type (CC-BY, etc.)
  - [ ] Link to original source

✅ **Claims accuracy** (CPFTA):

- [ ] Substantiate any claims about recipes:
  - [ ] ✅ "Recipe from [specific source]"
  - [ ] ✅ "Based on [cookbook]"
  - [ ] ❌ "Authentic" (without clear source)
  - [ ] ❌ "Chef-approved" (without actual chef approval)
- [ ] Include disclaimer: "Recipe information for personal use only. Verify ingredients before cooking."

---

### 2.5 United States

#### Applicable Laws

- **Copyright Law (17 U.S.C.)** - recipe copyright for creative works
- **FTC Act Section 5** - deceptive claims about recipes
- **Fair Use Doctrine** (17 U.S.C. §107) - limited recipe reproduction
- **State Consumer Protection Laws** - misleading recipe claims
- **Food Allergen Labeling and Consumer Protection Act (FALCPA, 21 U.S.C. §343(w))** - if the app displays allergen information alongside recipes, the accuracy of that information is governed by this Act; the 9 major US allergens must be correctly identified

#### Legal Risks

| Risk                              | Description                                                                    | Jurisdiction                                  |
| --------------------------------- | ------------------------------------------------------------------------------ | --------------------------------------------- |
| **Recipe copyright infringement** | Reproducing copyrighted recipe text/images without permission                  | 17 U.S.C. §106                                |
| **Fair Use boundary**             | Simple ingredient lists are not copyrightable, but formatted recipes may be    | 17 U.S.C. §102, Harper & Row v. Nation (1985) |
| **Deceptive "authentic" claims**  | Claiming recipe is "authentic Asian recipe" without substantiation             | FTC Act §5                                    |
| **Attribution/plagiarism**        | Reproducing recipe without crediting source may violate state laws, common law | State laws vary                               |
| **No copyright notice**           | Should display copyright information even if not legally required              | 17 U.S.C. §401 (best practice)                |

#### Required Actions

✅ **Recipe copyright compliance**:

- [ ] For each recipe, obtain one of:
  - [ ] Explicit written license from copyright holder
  - [ ] Use recipes under CC-BY, CC-BY-SA, or CC0 licenses
  - [ ] Original recipe created by app team
  - [ ] Recipes determined to be in Public Domain
- [ ] If relying on Fair Use:
  - [ ] Document Fair Use analysis for each recipe
  - [ ] Fair Use applies narrowly (commentary, criticism, education)
  - [ ] Transformative use: Must add significant value (analysis, variation)
  - [ ] Reproduce only minimum necessary text
  - [ ] Link to original source
  - **Note**: Relying on Fair Use is risky; obtaining licenses is safer
- [ ] Store and display:
  - [ ] Source attribution
  - [ ] License type
  - [ ] Copyright holder name
  - [ ] Original publication date

✅ **Claims substantiation** (FTC):

- [ ] Never claim recipe is:
  - ❌ "Authentic Asian recipe" unless sourced from verified cultural/culinary authority
  - ❌ "Chef-approved" unless actually approved
  - ❌ "Traditional" unless sourced from established cookbook/authority
- [ ] Substantiate claims with evidence:
  - ✅ "Recipe from [specific cookbook by recognized author]"
  - ✅ "Traditional dish from [region] as prepared in [source]"
  - ✅ "AI-assisted variation on [original recipe source]"
- [ ] Disclaimer: "Recipes for personal use. Verify cooking techniques before preparing."

---

### 2.6 Canada

#### Applicable Laws

- **Copyright Act (R.S.C., 1985, c. C-42)** - recipe copyright
- **PIPEDA/Quebec Law 25** (ingredient profiling is personal data)
- **Competition Act** - deceptive marketing claims
- **Safe Food for Canadians Regulations (SFCR, SOR/2018-108)** - if the app displays allergen or food labeling information, it must align with SFCR Schedule 9 (List of Priority Allergens); Canada requires disclosure of 14 priority allergens
- **Canadian Standards (CSA/ULC)** - food preparation guidance

#### Legal Risks

| Risk                      | Description                                                        | Jurisdiction               |
| ------------------------- | ------------------------------------------------------------------ | -------------------------- |
| **Recipe copyright**      | Creative recipes are copyright-protected; ingredient lists are not | Copyright Act Part I §5    |
| **Ingredient profiling**  | Analyzing cooking preferences requires PIPEDA/Quebec consent       | PIPEDA §4.2, Quebec Law 25 |
| **Deceptive marketing**   | Claiming recipe is "authentic" or "approved" without basis         | Competition Act §36        |
| **No French attribution** | Must provide recipe attribution in French (if Quebec market)       | Copyright Act §37, PIPEDA  |

#### Required Actions

✅ **Recipe sourcing and copyright**:

- [ ] Obtain licenses for all recipes:
  - [ ] Contact recipe creators for permission
  - [ ] Use CC-licensed recipes (CC-BY, CC-BY-SA)
  - [ ] Document licenses
- [ ] For each recipe, display:
  - [ ] "Recipe © [Year] [Author]. Used with permission."
  - [ ] "Original source: [URL/publication]"
  - [ ] License type
  - [ ] Translation to French if serving Quebec market

✅ **PIPEDA/Quebec Law 25 consent** (ingredient profiling):

- [ ] Obtain explicit consent for:
  - [ ] Collecting ingredient preferences
  - [ ] Analyzing preferences to recommend recipes
  - [ ] Profiling based on dietary patterns
- [ ] Provide notice in English and French (if Quebec market)

✅ **Competition Act compliance** (deceptive claims):

- [ ] Substantiate all recipe claims:
  - [ ] ✅ "Recipe from [specific, verifiable source]"
  - [ ] ❌ "Authentic Asian" (without cultural authority source)
  - [ ] ❌ "Endorsed by [celebrity]" (without actual endorsement)
- [ ] Provide substantiation on request

---

## 3. TRADE PERISHABLES

### 3.1 France

#### Applicable Laws

- **GDPR** (user profiles, transaction history, messaging)
- **French Civil Code (Code Civil)** - contract/liability for traded items
- **French Food Code (Code Alimentaire / Code Rural et de la Pêche Maritime)** - national food safety and trading
- **EU Regulation (EC) No 178/2002** - General Food Law: establishes general principles and requirements of EU food law, including traceability obligations and the "farm to fork" liability chain; applies directly in France
- **EU Regulation (EU) No 1169/2011** - Food Information to Consumers (FIC): mandates disclosure of 14 major allergens in any food information communication; **non-compliance is a criminal offense in France**
- **EU Regulation (EC) No 852/2004** - Hygiene of Foodstuffs: food hygiene requirements for food businesses; may apply if users are operating at commercial scale
- **Consumer Protection Code (Code de la Consommation)** - consumer rights
- **Digital Services Act (EU) 2022/2065 (DSA)** - liability of online platforms for user-generated content and marketplace activities; replaces Platform Directive for EU-based platforms

#### Legal Risks

| Risk                           | Description                                                                                              | Jurisdiction                              |
| ------------------------------ | -------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| **Food safety liability**      | Platform may be liable if traded food causes illness/harm                                                | French Civil Code Article 1240, Food Code |
| **No terms of service**        | Must have clear ToS defining liability limits and user responsibilities                                  | Consumer Protection Code Article L121-1   |
| **Personal data in messaging** | User messages may contain personal data (addresses, names) requiring GDPR safeguards                     | GDPR Articles 6, 9                        |
| **Platform content liability** | If platform facilitates illegal trades (spoiled food, undeclared allergens), platform is liable          | Platform Directive Article 4              |
| **B2C vs. C2C status**         | If platform is facilitating business sales (not just consumer-to-consumer), additional regulations apply | Consumer Protection Code                  |

#### Required Actions

✅ **Terms of Service**:

- [ ] Create comprehensive ToS in French defining:
  - [ ] Liability limits: "Platform is not liable for food quality, safety, or authenticity of traded items"
  - [ ] User responsibility: "Users are solely responsible for ensuring items are safe to trade and comply with food safety regulations"
  - [ ] Disclaimer: "Users must follow food safety laws; items must be properly stored and transported"
  - [ ] No warranty: "Platform provides marketplace only; does not verify food safety or quality"
  - [ ] Dispute resolution process
- [ ] Make ToS mandatory to accept before trading

✅ **Food safety disclaimer**:

- [ ] Add to app and ToS:
  - "IMPORTANT: Food items must comply with French food safety standards. Only trade non-perishable items or items that have been properly stored. Users assume full responsibility for food safety. Platform does not verify item safety or condition."
- [ ] Recommend users avoid trading perishables that require refrigeration or have short shelf lives

✅ **User data protection**:

- [ ] Implement GDPR safeguards for messaging/transaction data:
  - [ ] Privacy policy: "We collect minimal data to facilitate trades (names, contact info)"
  - [ ] Data retention: "Contact info is deleted after trade is complete (30 days retention)"
  - [ ] Encryption for messages in transit and at rest
  - [ ] User can request data deletion

✅ **Reporting and moderation**:

- [ ] Implement mechanism to report suspicious trades (spoiled food, illegal items)
- [ ] Respond to reports within 48 hours
- [ ] Document moderation actions (removals, bans) for compliance

---

### 3.2 Germany

#### Applicable Laws

- **GDPR** (user data, messaging)
- **Impressum** still required (TMG §7)
- **German Civil Code (BGB)** - contract liability, seller responsibility
- **LFGB (Lebensmittel- und Futtermittelgesetzbuch)** - German Food and Feed Code: primary national food safety statute; violations are criminal offenses under §58-60 LFGB
- **EU Regulation (EC) No 178/2002** - General Food Law: directly applicable in Germany; establishes food safety liability principles and traceability requirements across the supply chain
- **EU Regulation (EU) No 1169/2011** - Food Information to Consumers (FIC): **directly applicable**; mandates disclosure of 14 major allergens; failure to disclose allergens that cause harm creates both civil and criminal liability under LFGB §58
- **EU Regulation (EC) No 852/2004** - Food Hygiene: may apply to users operating at semi-commercial scale
- **Platform Liability Law (NetzDG - Network Enforcement Act)** - platform responsibility for illegal content
- **Digital Services Act (EU) 2022/2065 (DSA)** - supersedes NetzDG for some obligations; applies to online platforms in the EU
- **AGB (Allgemeine Geschäftsbedingungen)** - general terms and conditions

#### Legal Risks

| Risk                              | Description                                                                        | Jurisdiction     |
| --------------------------------- | ---------------------------------------------------------------------------------- | ---------------- |
| **Food safety liability**         | If platform facilitates trade of unsafe food, platform and seller both liable      | BGB §823, LFGB   |
| **Missing Impressum**             | Still required (as service provider)                                               | TMG §7           |
| **No clear AGB (ToS)**            | Must provide German-language terms and conditions                                  | BGB §305 et seq. |
| **Unlicensed food business**      | If users are operating as food businesses without licenses, platform may be liable | LFGB §4          |
| **No liability limits**           | If platform doesn't clearly limit liability, may be liable for user damage         | BGB §823         |
| **Inadequate content moderation** | Platform must remove illegal content within legal timeframes                       | NetzDG §3, §4    |

#### Required Actions

✅ **Impressum** (still required):

- [ ] See section 1.2 above for Impressum requirements

✅ **AGB (Terms & Conditions)** - in German:

- [ ] Create detailed AGB including:
  - [ ] **Liability disclaimer**: "Nutzer haften allein für Sicherheit und Qualität gehandelter Lebensmittel" (Users alone are liable for safety and quality of traded foods)
  - [ ] **Food safety obligation**: "Lebensmittel müssen den deutschen Lebensmittel- und Futtermittelgesetzbuch-Standards entsprechen" (Foods must comply with LFGB standards)
  - [ ] **No verification**: "Plattform überprüft nicht die Sicherheit oder Qualität von Lebensmitteln" (Platform does not verify food safety or quality)
  - [ ] **Prohibited items**: List prohibited items (spoiled food, items with removed labels, items without clear expiry)
  - [ ] **Indemnification**: Users indemnify platform against claims arising from their trades
  - [ ] **Cancellation rights**: Consumer rights to cancel trades (14 days for some items per consumer law)
- [ ] Make acceptance mandatory before use

✅ **Food safety compliance**:

- [ ] Prominent disclaimer:
      "WARNUNG: Plattform ist nicht verantwortlich für die Lebensmittelsicherheit. Nutzer müssen alle Lebensmittelgesetze einhalten. Handeln Sie nur mit sicheren, richtig gelagerten Lebensmitteln."
      (WARNING: Platform is not responsible for food safety. Users must comply with all food laws. Only trade safe, properly stored foods.)
- [ ] Educate users: Link to LFGB requirements and BfR (Federal Institute for Risk Assessment) guidelines
- [ ] Avoid trading of potentially dangerous items (raw meat, unpasteurized dairy, unlabeled items)

✅ **Content moderation** (NetzDG):

- [ ] Implement rapid removal of:
  - [ ] Illegal food trades (spoiled food, contaminated items)
  - [ ] Unlicensed food business operations
  - [ ] Items without proper labeling/allergen information
- [ ] Document removal decisions
- [ ] Provide user right to appeal removal

✅ **User data protection** (GDPR + BDSG):

- [ ] Privacy Policy in German and English
- [ ] Consent for storing contact info for trades
- [ ] Delete contact info after trade complete (30-day retention)
- [ ] Encryption for messaging

---

### 3.3 United Kingdom

#### Applicable Laws

- **UK-GDPR** (user data)
- **Consumer Rights Act 2015** - seller responsibility for goods
- **Food Safety Act 1990** - food safety standards; selling unsafe food is a criminal offense under §8
- **Food Information Regulations 2014 (SI 2014/1855)** - the UK post-Brexit equivalent of EU 1169/2011; **allergen disclosure for all 14 major allergens is mandatory**; failure to disclose allergens that cause harm creates criminal liability
- **Food Hygiene Regulations 2006 (SI 2006/14)** - food hygiene standards for anyone handling food for others; may apply to users trading food at scale
- **Environmental Health Act 1990** - public health responsibility
- **Fraud Act 2006** - if facilitating fraudulent trades
- **Public Liability** - platform liability for user actions

#### Legal Risks

| Risk                                  | Description                                                                   | Jurisdiction                 |
| ------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------- |
| **Seller liability for defects**      | Seller is liable if food is not fit for purpose or safe                       | Consumer Rights Act 2015 §9  |
| **Platform knowledge of unsafe food** | If platform knows or should know traded item is unsafe, platform is liable    | Consumer Rights Act 2015 §62 |
| **No terms limiting liability**       | If ToS doesn't clearly limit platform liability, platform may be fully liable | Consumer Rights Act 2015 §62 |
| **Food safety failure**               | Selling unsafe food is criminal offense                                       | Food Safety Act 1990 §8      |
| **No clear contractual basis**        | Users may claim trades were unfair if ToS not clear                           | Consumer Rights Act 2015 §62 |

#### Required Actions

✅ **Terms of Service**:

- [ ] Create comprehensive ToS including:
  - [ ] **Food safety responsibility**: "Sellers warrant that food items are safe, properly stored, and comply with UK food safety standards"
  - [ ] **Platform limitation of liability**: "Platform is not liable for food quality, safety, or fitness for purpose. Sellers are solely responsible."
  - [ ] **Disclaimer**: "Users must comply with Food Safety Act 1990 and UK food safety regulations"
  - [ ] **Prohibited items**: List items that cannot be traded (raw meat, unpasteurized dairy, items without allergen info)
  - [ ] **Indemnification**: Users indemnify platform against third-party claims
  - [ ] **Consumer rights**: Note that consumer rights under Consumer Rights Act 2015 cannot be waived
- [ ] Highlight key points clearly
- [ ] Require affirmative acceptance

✅ **Food safety compliance**:

- [ ] Prominent notice:
      "IMPORTANT: Only trade food items that are safe and comply with UK food safety standards (Food Safety Act 1990). You are responsible for food safety and must follow proper storage and hygiene practices. Non-perishable or shelf-stable items are safer to trade."
- [ ] Link to FSA (Food Standards Agency) guidance
- [ ] Provide list of prohibited items (allergen-undeclared items, expired items, etc.)

✅ **Content moderation**:

- [ ] Remove or suspend trades involving:
  - [ ] Items without allergen labeling
  - [ ] Expired items
  - [ ] Items indicating poor storage conditions
  - [ ] Claims of "cures" or health benefits
- [ ] Respond to safety reports quickly
- [ ] Document removal decisions

✅ **Insurance**:

- [ ] Consider obtaining public liability insurance in case of food-related claims
- [ ] Document insurance coverage in ToS

✅ **Data protection**:

- [ ] UK-GDPR compliance for user data
- [ ] Messaging encryption
- [ ] Delete contact info after trade (30-day retention)

---

### 3.4 Singapore

#### Applicable Laws

- **PDPA** (user data, messaging)
- **Sale of Goods Act (Cap. 393)** - seller responsibility for goods quality
- **Consumer Protection (Fair Trading) Act (CPFTA)** - unfair trades, misrepresentation
- **Sale of Food Act (Cap. 283)** - primary food safety statute; trading unsafe food is an offense
- **Food Regulations (Cap. 283, Rg 1)** - labeling standards including allergen disclosure requirements
- **Singapore Food Agency (SFA) Act 2019** - establishes SFA as the regulatory authority for all food safety matters; enforcement body for food safety violations
- **Environmental Public Health Act (EPHA, Cap. 95)** - food hygiene standards; applies to anyone handling food for others
- Note: "FSSA" as previously referenced is not a standalone statute; food safety is governed by the Sale of Food Act + SFA Act framework

#### Legal Risks

| Risk                             | Description                                                                     | Jurisdiction             |
| -------------------------------- | ------------------------------------------------------------------------------- | ------------------------ |
| **Seller liability for defects** | Goods must be of merchantable quality and fit for purpose                       | Sale of Goods Act §14    |
| **Misrepresentation in trades**  | If item is misrepresented (e.g., "fresh" when spoiled), seller is liable        | CPFTA §4                 |
| **Food safety violations**       | Trading unsafe food is criminal offense; platform may be liable if facilitating | FSSA §59                 |
| **Allergen non-disclosure**      | Failing to disclose allergens is offense                                        | FSSA §53, EPHA §125      |
| **No terms of service**          | Absence of clear ToS may render platform fully liable                           | Sale of Goods Act, CPFTA |

#### Required Actions

✅ **Terms of Service**:

- [ ] Create ToS in English (and Chinese, Malay if targeting broader audience) including:
  - [ ] **Seller responsibility**: "Sellers warrant items are safe, properly stored, and comply with Singapore food safety standards (FSSA, EPHA)"
  - [ ] **Platform disclaimer**: "Platform does not verify food safety or quality. Sellers are solely responsible for food safety."
  - [ ] **Allergen obligation**: "Sellers must disclose all known allergens. Failure to disclose is illegal."
  - [ ] **Prohibited items**: List items (raw meat, unpasteurized dairy, items without proper labeling, expired items)
  - [ ] **Liability limitation**: "Platform's liability is limited to [amount]. Users indemnify platform against third-party claims."
  - [ ] **Dispute resolution**: Provide mechanism for dispute resolution
- [ ] Require affirmative acceptance

✅ **Food safety and labeling**:

- [ ] Important notice:
      "SAFETY WARNING: Food items must comply with Singapore FSSA and EPHA standards. Sellers must disclose allergens and storage instructions. Platform does not verify food safety. You are responsible for following food safety practices. Non-perishable items recommended for safer trading."
- [ ] Educate users: Link to NEA (National Environment Agency) food safety guidelines
- [ ] Require disclosure of:
  - [ ] Allergens
  - [ ] Storage conditions
  - [ ] Expiry date/best-by date
  - [ ] Preparation method (if relevant)

✅ **Content moderation**:

- [ ] Monitor and remove trades involving:
  - [ ] Items without allergen disclosure
  - [ ] Raw or potentially unsafe items
  - [ ] Expired items
  - [ ] Items with removed labels
  - [ ] Suspicious quality claims
- [ ] Respond to safety reports within 24 hours
- [ ] Escalate reports to NEA if necessary

✅ **User data protection** (PDPA):

- [ ] Obtain consent for storing contact info
- [ ] Encrypt messaging and data in transit
- [ ] Delete contact info after trade (30-day retention max)
- [ ] Implement PDPA data subject rights

---

### 3.5 United States

#### Applicable Laws

- **No federal marketplace liability law** (platforms generally not liable under Section 230, 47 U.S.C. §230)
- **Food Safety Modernization Act (FSMA, 21 U.S.C. §2201)** - primary federal food safety law; establishes FDA authority over food safety practices; platforms facilitating food distribution should be aware of traceability and safety obligations
- **Food Allergen Labeling and Consumer Protection Act (FALCPA, 21 U.S.C. §343(w))** - requires declaration of 9 major allergens; if the platform facilitates food trade, sellers must disclose allergens; platform should enforce this requirement
- **21 CFR Part 101** - FDA food labeling regulations; traded food items must comply with labeling standards
- **State food safety and cottage food laws** - vary significantly by state; many states have "cottage food laws" (e.g., California Homemade Food Act, AB 1616) that exempt certain home-produced food trades from licensing — but these exemptions have scope limits and do NOT override allergen disclosure or safety requirements
- **FTC Act Section 5** - deceptive food claims
- **Tort law** - platform liability if failing to prevent foreseeable harm
- **State consumer protection laws** - vary widely
- **UCC (Uniform Commercial Code)** §2-607, §2-708 - sales law (varies by state)

#### Legal Risks

| Risk                        | Description                                                               | Jurisdiction              |
| --------------------------- | ------------------------------------------------------------------------- | ------------------------- |
| **No liability protection** | Section 230 may not apply to platforms facilitating dangerous food trades | 47 U.S.C. §230            |
| **Tort liability**          | If platform knows or should know of danger and fails to prevent, liable   | Common law                |
| **Food safety claims**      | Deceptive claims about food safety/quality                                | FTC Act §5                |
| **State variations**        | Food laws vary by state; some states have stricter requirements           | State laws vary           |
| **Allergen non-disclosure** | Failing to disclose allergens could lead to injury liability              | Tort law, FDA regulations |
| **No clear disclaimers**    | If ToS doesn't clearly disclaim liability, platform is fully liable       | Tort law, UCC             |

#### Required Actions

✅ **Terms of Service** (comprehensive):

- [ ] Create detailed ToS including:
  - [ ] **User responsibility**: "You are solely responsible for food safety, quality, and legality of trades"
  - [ ] **Seller warranty**: "Sellers warrant items are safe and comply with FDA and local food safety standards"
  - [ ] **Allergen disclosure**: "Sellers must disclose all known allergens. Non-disclosure is prohibited."
  - [ ] **Prohibited items**: Clearly list prohibited items:
    - Raw meat (unless properly packaged/labeled)
    - Unpasteurized dairy
    - Items without labels/allergen info
    - Expired items
    - Items with signs of contamination
  - [ ] **Liability disclaimer**:
    ```
    DISCLAIMER: PLATFORM IS NOT RESPONSIBLE FOR FOOD SAFETY, QUALITY, OR
    COMPLIANCE WITH FOOD SAFETY LAWS. USERS ASSUME FULL RESPONSIBILITY FOR
    VERIFYING FOOD SAFETY. PLATFORM DOES NOT GUARANTEE ITEMS ARE FIT FOR
    CONSUMPTION.
    ```
  - [ ] **Limitation of liability**: "Platform's liability limited to [amount or refund amount]"
  - [ ] **Indemnification**: Users indemnify platform
  - [ ] **Dispute resolution**: Arbitration clause (recommended)
- [ ] Make ToS mandatory and prominent
- [ ] Update ToS every 12 months as laws evolve

✅ **Food safety education**:

- [ ] Add prominent disclaimers in app:
      "IMPORTANT: This is a peer-to-peer marketplace. Food safety is the responsibility of the seller and buyer. Before trading for food:\n
  - Only trade non-perishable items or items that are clearly safe\n
  - Verify items are properly labeled and stored\n
  - Disclose any allergies or dietary restrictions\n
  - Follow FDA food safety guidelines at fda.gov"
- [ ] Link to FDA food safety guidance: fda.gov/food/foodborne-illnesses
- [ ] Consider restricting trades to non-perishable items only

✅ **Content moderation**:

- [ ] Monitor and suspend trades involving:
  - [ ] Raw or undercooked meat
  - [ ] Unpasteurized dairy
  - [ ] Items without allergen labels
  - [ ] Expired items (if past expiry date)
  - [ ] Items with visible contamination
  - [ ] Claims of health benefits ("cures illness," etc.)
- [ ] Respond to safety reports promptly
- [ ] Document actions taken
- [ ] Consider escalating to state health departments if serious violations

✅ **Insurance and legal protection**:

- [ ] Obtain general liability insurance
- [ ] Consider food safety/product liability insurance
- [ ] Document platform's safety policies and moderation efforts
- [ ] Keep detailed records of moderation actions (removals, warnings, bans)

---

### 3.6 Canada

#### Applicable Laws

- **PIPEDA/Quebec Law 25** (user data, messaging)
- **CASL** (marketing/notification messaging)
- **Safe Food for Canadians Act (SFCA, S.C. 2012, c. 24)** - primary federal food safety statute; replaced much of the Food and Drugs Act for food safety; governs food handling, labeling, traceability, and import/export
- **Safe Food for Canadians Regulations (SFCR, SOR/2018-108)** - Schedule 9 lists 14 priority allergens; **allergen disclosure is mandatory**; non-disclosure that causes harm can result in criminal charges
- **Food and Drugs Act (R.S.C., 1985, c. F-27)** - still governs food safety standards and adulteration; §4 prohibits selling unsafe food; §5 prohibits misrepresentation
- **Consumer Protection Act (varies by province)** - provincial consumer rights
- **Sale of Goods Act (varies by province)** - seller responsibility
- **Provincial Food Safety Standards** (vary by province, overseen by CFIA - Canadian Food Inspection Agency)

#### Legal Risks

| Risk                        | Description                                                                     | Jurisdiction                               |
| --------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------ |
| **Food safety violations**  | Trading unsafe food violates Food and Drugs Act; criminal offense               | Food and Drugs Act §4, §5                  |
| **Allergen non-disclosure** | Undeclared allergens can cause injury and violation of labeling requirements    | Food and Drugs Act §6, CFIA regulations    |
| **Seller liability**        | Sellers liable for defects; platform may be liable if facilitating unsafe trade | Sale of Goods Act (provincial), Common law |
| **No clear terms**          | Absence of clear ToS may render platform fully liable                           | Consumer Protection Act (provincial)       |
| **CASL violations**         | If sending trade notifications/reminders, could violate CASL                    | CASL §6                                    |
| **Messaging privacy**       | User contact info in messaging requires PIPEDA/Quebec consent                   | PIPEDA §4.2, Quebec Law 25                 |

#### Required Actions

✅ **Terms of Service** (in English and French):

- [ ] Create comprehensive ToS in English and French (mandatory for Quebec market) including:
  - [ ] **User responsibility**: "You are solely responsible for food safety and compliance with Canadian Food and Drugs Act and provincial regulations"
  - [ ] **Seller warranty**: "Sellers warrant items are safe, properly labeled, comply with CFIA standards, and all allergens are disclosed"
  - [ ] **Allergen disclosure**: "CRITICAL: Sellers must disclose ALL known allergens. Non-disclosure is prohibited and may result in criminal charges."
  - [ ] **Prohibited items**: List prohibited items (raw meat unless packaged, unpasteurized dairy, items without proper labeling, expired items, items with unknown ingredients)
  - [ ] **Liability disclaimer**:
    ```
    IMPORTANT: This platform facilitates peer-to-peer food trading. We do NOT verify food safety or quality.
    SELLERS AND BUYERS ARE SOLELY RESPONSIBLE FOR FOOD SAFETY. Follow Health Canada and CFIA guidelines.
    Platform has NO LIABILITY for illness, injury, or harm caused by food items.
    ```
  - [ ] **Liability limitation**: "Platform's liability is limited to [amount]. Users indemnify platform."
  - [ ] **Dispute resolution**: Include dispute resolution process
- [ ] Require affirmative, non-pre-checked acceptance
- [ ] Update annually to reflect regulatory changes

✅ **Food safety compliance**:

- [ ] Prominent safety warning:

  ```
  AVERTISSEMENT DE SÉCURITÉ / FOOD SAFETY WARNING:
  Ce marché est un service peer-to-peer. La sécurité des aliments est la responsabilité
  exclusive du vendeur et de l'acheteur. Seuls les articles non périssables ou clairement sûrs
  doivent être échangés. Consultez les directives de Santé Canada et de l'ACIA.

  This marketplace is a peer-to-peer service. Food safety is the sole responsibility of the
  seller and buyer. Only non-perishable or clearly safe items should be traded. Consult Health
  Canada and CFIA guidelines.
  ```

- [ ] Link to:
  - [ ] Health Canada food safety: www.canada.ca/health-food-safety
  - [ ] CFIA (Canadian Food Inspection Agency): www.inspection.canada.ca
  - [ ] Provincial health ministry guides
- [ ] Require sellers to disclose:
  - [ ] Full ingredient list (if known)
  - [ ] All allergens (mandatory disclosure)
  - [ ] Storage conditions
  - [ ] Best-by/expiry date
  - [ ] Preparation method (if relevant)
  - [ ] Any recalls or safety concerns

✅ **Content moderation**:

- [ ] Remove or suspend trades involving:
  - [ ] Raw or potentially unsafe meat
  - [ ] Unpasteurized dairy
  - [ ] Items without proper allergen disclosure
  - [ ] Expired items
  - [ ] Items with unknown composition
  - [ ] Items subject to CFIA recalls
- [ ] Respond to safety reports within 24 hours
- [ ] Keep detailed moderation logs
- [ ] Escalate serious violations to provincial health authorities if necessary

✅ **PIPEDA/Quebec Law 25 compliance** (user data):

- [ ] Obtain explicit consent for:
  - [ ] Collecting contact info (name, phone, address)
  - [ ] Storing contact info for trade transactions
  - [ ] Using data to facilitate trades
- [ ] Provide notice in English and French: "We collect your contact information to facilitate secure trades. Data is deleted 30 days after trade completion."
- [ ] Delete contact info after trade (maximum 30-day retention)
- [ ] Encrypt messages and contact data in transit and at rest
- [ ] Implement PIPEDA data subject rights (access, correction, deletion)

✅ **CASL compliance** (notifications/messaging):

- [ ] If sending trade notifications (trade matched, buyer ready, etc.):
  - [ ] Obtain prior express consent (opt-in)
  - [ ] Do NOT use pre-checked boxes
  - [ ] Include in every message:
    - [ ] Clear sender identification ("Asian Auntie Marketplace")
    - [ ] Easy unsubscribe mechanism (link or email address)
    - [ ] Postal mailing address
  - [ ] Honor unsubscribe requests within 10 business days
- [ ] Do NOT send unsolicited marketing messages

---

## Summary: Jurisdiction-Specific Checklists

### Manage Perishables

| Jurisdiction  | Key Requirements                                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **France**    | ✅ GDPR compliance, Privacy Policy (French), DPIA for profiling, Cookie banner with explicit consent                      |
| **Germany**   | ✅ Impressum (legal notice), GDPR compliance, Privacy Policy (German), DPA with processors, Encryption                    |
| **UK**        | ✅ UK-GDPR compliance, Privacy Notice, Consumer Rights, PECR (no marketing emails without consent), SAR mechanism         |
| **Singapore** | ✅ PDPA Privacy Policy, Consent (mostly can be deemed), Cross-border transfer assessment, Data subject rights             |
| **US**        | ✅ CCPA (if California users), Privacy Policy, Consumer rights, FTC compliance, Food safety disclaimers                   |
| **Canada**    | ✅ PIPEDA/Quebec Law 25 compliance, Privacy Policy (French + English for Quebec), CASL compliance (no marketing), Consent |

### Recommend Recipes

| Jurisdiction  | Key Requirements                                                                                                       |
| ------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **France**    | ✅ GDPR (ingredient profiling), Privacy Policy, Recipe copyright licenses, Attribution, Disclaimer                     |
| **Germany**   | ✅ Impressum, GDPR, Copyright compliance, Recipe licenses, AI transparency (future), Attribution                       |
| **UK**        | ✅ UK-GDPR, Copyright licenses, Attribution, Claims substantiation (Consumer Rights Act), Avoid misleading claims      |
| **Singapore** | ✅ PDPA consent for profiling, Copyright compliance, Attribution, CPFTA claims substantiation                          |
| **US**        | ✅ Copyright licenses or Fair Use analysis, Attribution, FTC compliance (no deceptive claims), Food safety disclaimers |
| **Canada**    | ✅ PIPEDA/Quebec Law 25 (profiling consent), Copyright compliance, Attribution, Competition Act (substantiate claims)  |

### Trade Perishables

| Jurisdiction  | Key Requirements                                                                                               |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| **France**    | ✅ ToS (French), Liability limits, Food safety disclaimer, GDPR (messaging data), Content moderation           |
| **Germany**   | ✅ Impressum, AGB (German), Food safety (LFGB), Liability limits, Content moderation, NetzDK compliance        |
| **UK**        | ✅ ToS, Consumer Rights Act compliance, Food Safety Act warnings, Seller liability, Public liability insurance |
| **Singapore** | ✅ ToS, FSSA/EPHA food safety, Allergen disclosure requirement, Sale of Goods Act, PDPA (messaging)            |
| **US**        | ✅ ToS (detailed), Food safety education (FDA), Liability disclaimers, Content moderation, Insurance           |
| **Canada**    | ✅ ToS (English + French), Food and Drugs Act compliance, CFIA guidelines, CASL (notifications), PIPEDA        |

---

## General Recommendations

### Immediate Actions (All Jurisdictions)

1. **Create Privacy Policy** covering all three features

   - [ ] Specify data collected
   - [ ] Specify purposes
   - [ ] Specify lawful basis
   - [ ] Specify retention periods
   - [ ] List third-party processors
   - [ ] Include consumer rights

2. **Create Terms of Service / Acceptable Use Policy**

   - [ ] Define user responsibilities
   - [ ] Limit platform liability
   - [ ] Clarify prohibited content/trades
   - [ ] Include indemnification clause
   - [ ] Specify dispute resolution

3. **Implement Consent Management**

   - [ ] Explicit opt-in (not pre-checked boxes)
   - [ ] Separate consents (marketing, analytics, data processing)
   - [ ] Easy withdrawal mechanism
   - [ ] Document consent timestamps

4. **Jurisdiction-Specific Translations**
   - [ ] France: Privacy Policy + ToS in French
   - [ ] Germany: Impressum (required), Privacy Policy + ToS in German
   - [ ] UK: Privacy Notice in English
   - [ ] Singapore: Privacy Policy in English
   - [ ] US: Privacy Policy in English
   - [ ] Canada: Privacy Policy + ToS in English and French

### Medium-Term Actions (Next 3-6 months)

1. **Implement Data Subject Rights**

   - [ ] Access (download data in machine-readable format)
   - [ ] Correction (update inaccurate data)
   - [ ] Erasure (delete data)
   - [ ] Portability (export data)
   - [ ] Opt-out of profiling/analytics

2. **Security & Encryption**

   - [ ] SSL/TLS for all data in transit
   - [ ] Encryption for sensitive data at rest
   - [ ] Secure password hashing
   - [ ] Rate limiting on login attempts
   - [ ] Audit logging for admin actions

3. **Content Moderation**

   - [ ] Implement flagging/reporting mechanism
   - [ ] Response SLAs (24-48 hours)
   - [ ] Moderation logs/audit trail
   - [ ] Appeal process for removed content
   - [ ] Escalation to authorities if illegal activity

4. **Recipe Attribution & Licensing**
   - [ ] Audit all recipes in database
   - [ ] Obtain licenses or verify CC-license compliance
   - [ ] Add attribution metadata
   - [ ] Display source and license on each recipe
   - [ ] Document Fair Use analysis (US) or licenses

### Long-Term Actions (6-12 months)

1. **Specialized Legal Advice**

   - [ ] Consult local lawyer in each jurisdiction
   - [ ] Conduct DPIA (France, Germany, UK, Singapore)
   - [ ] Review insurance needs (especially for Trade feature)
   - [ ] Establish vendor agreements with third-party processors

2. **Emerging Regulations**

   - [ ] Monitor AI regulation developments (Germany, EU, US)
   - [ ] Watch for platform regulation changes
   - [ ] Track food safety standard updates
   - [ ] Assess if DSA (Digital Services Act) applies in EU

3. **Accessibility & Inclusivity**
   - [ ] WCAG 2.1 AA compliance (accessibility)
   - [ ] Multi-language support (especially French/German)
   - [ ] Inclusive design for diverse users

---

## Risk Priority Matrix

### High Risk (Address Immediately)

- ❌ **No Terms of Service for Trade Perishables** → Platform fully liable for user trades
- ❌ **No Food Safety Disclaimers** → Criminal liability, user injury claims
- ❌ **No Privacy Policy** → Violations of GDPR, PDPA, PIPEDA, CCPA (potential fines)
- ❌ **No Consent for Data Collection** → GDPR/PDPA violations (fines up to 4% of revenue or €20M)
- ❌ **No Impressum (Germany)** → Criminal offense, fine up to €5,000-€50,000

### Medium Risk (Address in 1-3 months)

- ⚠️ **No Recipe Attribution/Licenses** → Copyright infringement, takedown notices
- ⚠️ **No CASL Compliance (Canada)** → Fine up to $1M-$15M CAD per violation
- ⚠️ **No Data Subject Rights** → GDPR/PDPA violations
- ⚠️ **No Content Moderation** → Platform liability for harmful user content

### Lower Risk (Address within 6 months)

- ℹ️ **No DPIA documentation** → GDPR best practice (not critical if no high-risk processing)
- ℹ️ **Missing accessibility** → WCAG AA compliance (recommended, not always legally required)
- ℹ️ **Incomplete audit trail** → Best practice, helpful for incident response

---

## Next Steps

1. **Rank actions by jurisdiction where app will launch first**

   - If US-focused: CCPA, Food safety, liability disclaimers first
   - If EU-focused: GDPR, Impressum, privacy policy first
   - If Singapore-focused: PDPA, food safety (FSSA), ToS first

2. **Allocate resources**

   - Legal review (local lawyers)
   - Engineering (consent implementation, data deletion, encryption)
   - Product (disclaimer design, content moderation)

3. **Timeline planning**
   - Bare minimum: 4-6 weeks to address high-risk items
   - Comprehensive: 3-6 months for all medium-risk items

---

**Document Status**: Draft
**Last Updated**: April 2026
**Reviewed By**: [Your name/team]
**Next Review**: July 2026 (quarterly review recommended)
