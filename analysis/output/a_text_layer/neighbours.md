# Top-10 text neighbours, formation 2024-07-01

Text-only networks built from public SEC 10-K text; names from SEC EDGAR. Dense = centred bge-small cosine; BoW nouns = binary noun/proper-noun vectors (vocabulary from the prior 12 months). The version with TNIC-3 peers and SIC-3 marks (firm-level TNIC/CRSP data, SPEC §2) stays local: neighbours_full.md.

**AAPL** — Apple

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Best Buy; Verizon Communications; Gamestop; Amazon Com; Digital Turbine; Emerson Radio; Playboy; Inuvo; Mattel; Peloton Interactive |
| BoW nouns | Sonos; Arlo Technologies; Voxx International; Harmonic; Fubotv; Roku; Xperi; Gopro; Microsoft; Electronic Arts |
| BoW nouns / (m_i m_j) | Electronic Arts; Socket Mobile; Weyco Group; Escalade; Sonos; Educational Development; Digital Turbine; Gamestop; Sturm Ruger & Co; Steel Connect Llc |
| BoW nouns − (m_i+m_j)/2 | Sonos; Electronic Arts; Voxx International; Arlo Technologies; Harmonic; Fubotv; Roku; Gopro; Mattel; Corsair Gaming |
| BoW nouns − m_i m_j/med(m) | Sonos; Electronic Arts; Voxx International; Harmonic; Fubotv; Arlo Technologies; Roku; Gopro; Mattel; Corsair Gaming |

**MSFT** — Microsoft

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Unisys; Dynatrace; Grid Dynamics Holdings; Appian; Workday; Korn Ferry; Dropbox; Pagerduty; Servicenow; Digitalocean Holdings |
| BoW nouns | Adobe; Oracle; Nutanix; Palo Alto Networks; Servicenow; Crowdstrike Holdings; Manhattan Associates; Hp; C3.Ai; Confluent |
| BoW nouns / (m_i m_j) | International Business Mach…; Unity Software; Electronic Arts; Rackspace Technology; Csp; Nutanix; Educational Development; Inuvo; Progress Software; Zedge |
| BoW nouns − (m_i+m_j)/2 | Adobe; Oracle; Nutanix; Rackspace Technology; Servicenow; Hp; Okta; Palo Alto Networks; Confluent; Informatica |
| BoW nouns − m_i m_j/med(m) | Nutanix; Oracle; Adobe; Rackspace Technology; Okta; Servicenow; Teradata; International Business Mach…; Hp; Confluent |

**NVDA** — Nvidia

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Innodata; Appian; Dynatrace; Altair Engineering; Palantir Technologies; Microsoft; C3.Ai; Grid Dynamics Holdings; Snowflake; Mongodb |
| BoW nouns | Advanced Micro Devices; Qualcomm; Marvell Technology; Gsi Technology; Synopsys; Infinera; Xperi; Ansys; One Stop Systems; Ciena |
| BoW nouns / (m_i m_j) | Chicago Rivet & Machine; International Business Mach…; Advanced Micro Devices; Unity Software; Ceva; Adeia; Applied Digital; Pixelworks; Marvell Technology; Rambus |
| BoW nouns − (m_i+m_j)/2 | Advanced Micro Devices; Qualcomm; Marvell Technology; Gsi Technology; Synopsys; Xperi; Infinera; Ceva; Ansys; Broadcom |
| BoW nouns − m_i m_j/med(m) | Advanced Micro Devices; Qualcomm; Marvell Technology; Gsi Technology; Ceva; Xperi; Synopsys; Pixelworks; Infinera; Broadcom |

**JPM** — Jpmorgan Chase & Co

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Bank Of America; State Street; Oceanfirst Financial; Ameriserv Financial; Nicolet Bankshares; Wesbanco; Bank Of Hawaii; Comerica; Fnb; Trustco Bank Corp N Y |
| BoW nouns | Bank Of America; Northern Trust; Goldman Sachs Group; Keycorp; Pnc Financial Services Group; Us Bancorp De; Huntington Bancshares; Truist Financial; Capital One Financial; Fifth Third Bancorp |
| BoW nouns / (m_i m_j) | Wells Fargo & Company; Bank Of America; Bank Of New York Mellon; Umb Financial; Penns Woods Bancorp; Commerce Bancshares; Acnb; Patriot National Bancorp; Capital Bancorp; Independent Bank |
| BoW nouns − (m_i+m_j)/2 | Bank Of America; Northern Trust; Keycorp; Pnc Financial Services Group; Wells Fargo & Company; Goldman Sachs Group; Us Bancorp De; Truist Financial; Huntington Bancshares; Fifth Third Bancorp |
| BoW nouns − m_i m_j/med(m) | Bank Of America; Northern Trust; Wells Fargo & Company; Keycorp; Pnc Financial Services Group; Us Bancorp De; Fifth Third Bancorp; Truist Financial; Goldman Sachs Group; Huntington Bancshares |

**GS** — Goldman Sachs Group

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Moelis & Co; Lazard; Jefferies Financial Group; Houlihan Lokey; Stonex Group; Evercore; Piper Sandler Companies; Oppenheimer Holdings; Stepstone Group; Price T Rowe Group |
| BoW nouns | Us Bancorp De; M&T Bank; Keycorp; Northern Trust; Ally Financial; Capital One Financial; State Street; Fifth Third Bancorp; Bancfirst; Fnb |
| BoW nouns / (m_i m_j) | Hawthorn Bancshares; Wells Fargo & Company; First Community Bankshares; Independent Bank; Jpmorgan Chase & Co; First Hawaiian; Commerce Bancshares; Umb Financial; First National; Bankfinancial |
| BoW nouns − (m_i+m_j)/2 | Us Bancorp De; M&T Bank; Keycorp; Northern Trust; Fifth Third Bancorp; Capital One Financial; State Street; Jpmorgan Chase & Co; Ally Financial; Pnc Financial Services Group |
| BoW nouns − m_i m_j/med(m) | M&T Bank; Us Bancorp De; Keycorp; Fifth Third Bancorp; Northern Trust; Jpmorgan Chase & Co; First Hawaiian; Capital One Financial; Old National Bancorp; State Street |

**JNJ** — Johnson & Johnson

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Abbvie; Assertio Holdings; Abbott Laboratories; Organon & Co; Eli Lilly & Co; Gilead Sciences; Koru Medical Systems; Viridian Therapeutics, Inc.…; Supernus Pharmaceuticals; Ptc Therapeutics |
| BoW nouns | Abbvie; Bristol Myers Squibb; Pfizer; Merck & Co; Regeneron Pharmaceuticals; Eli Lilly & Co; Bioxcel Therapeutics; Esperion Therapeutics; Blueprint Medicines; Akebia Therapeutics |
| BoW nouns / (m_i m_j) | Sunshine Biopharma; Xoma Royalty; Rocket One; Abbvie; Corcept Therapeutics; Avalo Therapeutics; Abbott Laboratories; Cardiff Oncology; Checkpoint Therapeutics; Option Care Health |
| BoW nouns − (m_i+m_j)/2 | Abbvie; Bristol Myers Squibb; Pfizer; Merck & Co; Regeneron Pharmaceuticals; Corcept Therapeutics; Abbott Laboratories; Eli Lilly & Co; Cerevel Therapeutics Holdin…; Ironwood Pharmaceuticals |
| BoW nouns − m_i m_j/med(m) | Abbvie; Bristol Myers Squibb; Pfizer; Merck & Co; Corcept Therapeutics; Abbott Laboratories; Regeneron Pharmaceuticals; Cerevel Therapeutics Holdin…; Eli Lilly & Co; Ironwood Pharmaceuticals |

**PFE** — Pfizer

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Enzo Biochem; Cytokinetics; Repligen; Harvard Bioscience; Maravai Lifesciences Holdin…; Abeona Therapeutics; Organon & Co; Bio-Techne; Biocryst Pharmaceuticals; Bristol Myers Squibb |
| BoW nouns | Bristol Myers Squibb; Amgen; Invivyd; Bridgebio Pharma; Abbvie; Amneal Pharmaceuticals; Io Biotech; Dynavax Technologies; G1 Therapeutics; Elicio Therapeutics |
| BoW nouns / (m_i m_j) | Cocrystal Pharma; Sunshine Biopharma; Avalo Therapeutics; Rocket One; Xoma Royalty; Pulmatrix; Eton Pharmaceuticals; Cardiff Oncology; Abbvie; Organon & Co |
| BoW nouns − (m_i+m_j)/2 | Bristol Myers Squibb; Amgen; Abbvie; Dynavax Technologies; Invivyd; Eli Lilly & Co; Bridgebio Pharma; Io Biotech; Arcus Biosciences; Tempest Therapeutics |
| BoW nouns − m_i m_j/med(m) | Bristol Myers Squibb; Abbvie; Amgen; Avalo Therapeutics; Eton Pharmaceuticals; Tempest Therapeutics; Organon & Co; Dynavax Technologies; Arcus Biosciences; Xenetic Biosciences |

**KO** — Coca Cola

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Keurig Dr Pepper; Monster Beverage; Coca-Cola Consolidated; Westrock Coffee; Vita Coco Company; National Beverage; Pactiv Evergreen; Celsius Holdings; Bonk; Performance Food Group |
| BoW nouns | Pepsico; Coca-Cola Consolidated; Monster Beverage; Celsius Holdings; Keurig Dr Pepper; National Beverage; Zevia Pbc; Vita Coco Company; Molson Coors Beverage; Boston Beer |
| BoW nouns / (m_i m_j) | Pepsico; Coca-Cola Consolidated; Berry Global Group; Keurig Dr Pepper; Celsius Holdings; Barfresh Food Group; National Beverage; Monster Beverage; Vita Coco Company; J&J Snack Foods |
| BoW nouns − (m_i+m_j)/2 | Pepsico; Coca-Cola Consolidated; Monster Beverage; Celsius Holdings; Keurig Dr Pepper; National Beverage; Zevia Pbc; Vita Coco Company; Molson Coors Beverage; Mondelez International |
| BoW nouns − m_i m_j/med(m) | Pepsico; Coca-Cola Consolidated; Monster Beverage; Celsius Holdings; Keurig Dr Pepper; National Beverage; Vita Coco Company; Zevia Pbc; Mondelez International; Molson Coors Beverage |

**WMT** — Walmart

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Urban Outfitters; Dollar General; Hibbett; Arhaus; Target; Phillips Edison & Company; Foot Locker; Williams Sonoma; Grocery Outlet Holding; Tjx Companies |
| BoW nouns | Costco Wholesale; Bj'S Wholesale Club Holdings; Dollar General; Pricesmart; Tjx Companies; Former Bl Stores; Dollar Tree; Childrens Place; Ross Stores; Etsy |
| BoW nouns / (m_i m_j) | Costco Wholesale; Weyco Group; Dollar General; Ross Stores; Gamestop; Weis Markets; Amcon Distributing; Build-A-Bear Workshop; Tjx Companies; Pricesmart |
| BoW nouns − (m_i+m_j)/2 | Costco Wholesale; Bj'S Wholesale Club Holdings; Dollar General; Pricesmart; Tjx Companies; Former Bl Stores; Ross Stores; Dollar Tree; Childrens Place; Kroger |
| BoW nouns − m_i m_j/med(m) | Costco Wholesale; Bj'S Wholesale Club Holdings; Dollar General; Pricesmart; Tjx Companies; Ross Stores; Former Bl Stores; Dollar Tree; Childrens Place; Kroger |

**HD** — Home Depot

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Floor & Decor Holdings; Lowes Companies; Sonida Senior Living; Green Brick Partners; Bluelinx Holdings; Wayfair; Toll Brothers; American Woodmark; Taylor Morrison Home; Neighborhood Intelligence |
| BoW nouns | Lowes Companies; Ulta Beauty; Aaron'S Company; Floor & Decor Holdings; Willscot Holdings; Etsy; Ll Flooring Holdings; Destination Xl Group; Sleep Number; Walmart |
| BoW nouns / (m_i m_j) | Lowes Companies; Tile Shop Holdings; Masco; Floor & Decor Holdings; Gamestop; Dillard'S; Foot Locker; Build-A-Bear Workshop; Wayfair; Kohls |
| BoW nouns − (m_i+m_j)/2 | Lowes Companies; Ulta Beauty; Floor & Decor Holdings; Ll Flooring Holdings; Destination Xl Group; Walmart; Aaron'S Company; Zillow Group; Container Store Group; O Reilly Automotive |
| BoW nouns − m_i m_j/med(m) | Lowes Companies; Floor & Decor Holdings; Ulta Beauty; Tile Shop Holdings; Walmart; Autozone; Ll Flooring Holdings; Carters; Destination Xl Group; Zillow Group |

**BA** — Boeing

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Barnes Group; Lockheed Martin; General Dynamics; Spirit Aerosystems Holdings; Textron; Vse; Air Industries Group; Transdigm Group; Curtiss Wright; Moog |
| BoW nouns | Lockheed Martin; Rtx; Huntington Ingalls Industri…; Spirit Aerosystems Holdings; General Dynamics; Aerovironment; Hexcel; L3Harris Technologies; Triumph Group; Kratos Defense & Security S… |
| BoW nouns / (m_i m_j) | Mays J W; Healthcare Services Group; Lockheed Martin; Rtx; Mexco Energy; Sifco Industries; Servotronics; U.S. Goldmining; Spirit Aerosystems Holdings; Envue Medical |
| BoW nouns − (m_i+m_j)/2 | Lockheed Martin; Rtx; Spirit Aerosystems Holdings; Huntington Ingalls Industri…; General Dynamics; Hexcel; L3Harris Technologies; Triumph Group; Textron; Aerovironment |
| BoW nouns − m_i m_j/med(m) | Lockheed Martin; Rtx; Spirit Aerosystems Holdings; Huntington Ingalls Industri…; L3Harris Technologies; Triumph Group; Hexcel; Textron; General Dynamics; Aar |

**DAL** — Delta Air Lines

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Jetblue Airways; Alaska Air Group; Gogo; Hawaiian Holdings; General Dynamics; Southwest Airlines; Surf Air Mobility; Clear Secure; Wheels Up Experience; Skywest |
| BoW nouns | American Airlines Group; Alaska Air Group; Frontier Group Holdings; United Airlines Holdings; Allegiant Travel; Sun Country Airlines Holdin…; Southwest Airlines; Jetblue Airways; Hawaiian Holdings; Republic Airways Holdings |
| BoW nouns / (m_i m_j) | American Airlines Group; Aemetis; Alaska Air Group; Sun Country Airlines Holdin…; Hawaiian Holdings; Strata Critical Medical; Mexco Energy; Skywest; Frontier Group Holdings; United Airlines Holdings |
| BoW nouns − (m_i+m_j)/2 | American Airlines Group; Alaska Air Group; Frontier Group Holdings; Sun Country Airlines Holdin…; United Airlines Holdings; Allegiant Travel; Jetblue Airways; Southwest Airlines; Hawaiian Holdings; Republic Airways Holdings |
| BoW nouns − m_i m_j/med(m) | American Airlines Group; Alaska Air Group; Sun Country Airlines Holdin…; Frontier Group Holdings; United Airlines Holdings; Allegiant Travel; Jetblue Airways; Hawaiian Holdings; Southwest Airlines; Republic Airways Holdings |

**TSLA** — Tesla

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Phoenix Motor; Canoo; Beam Global; Rivian Automotive, Inc. / De; Microvast Holdings; Xos; Quantumscape; Azio Ai Holdings; Lucid Group; Visteon |
| BoW nouns | General Motors; Canoo; Rivian Automotive, Inc. / De; Nikola; Cenntro; Ford Motor; Lucid Group; Fluence Energy; Forza X1; Faraday Future Intelligent … |
| BoW nouns / (m_i m_j) | Phoenix Motor; General Motors; Canoo; Rivian Automotive, Inc. / De; Sunation Energy; American Battery Technology; Eos Energy Enterprises; Xos; Fabric.Ai; Bollinger Innovations |
| BoW nouns − (m_i+m_j)/2 | General Motors; Canoo; Rivian Automotive, Inc. / De; Cenntro; Nikola; Fluence Energy; Ford Motor; Lucid Group; Xos; Forza X1 |
| BoW nouns − m_i m_j/med(m) | General Motors; Canoo; Rivian Automotive, Inc. / De; Phoenix Motor; Xos; Cenntro; Fluence Energy; Bollinger Innovations; Nikola; Azio Ai Holdings |

**NFLX** — Netflix

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Gaia; Funko; Kartoon Studios; Paradium.Ai; Roku; Vimeo; Brightcove; Warner Music Group; Take Two Interactive Softwa…; Beasley Broadcast Group |
| BoW nouns | Gaia; Curiositystream; Roku; Buzzfeed; Chicken Soup For The Soul E…; Hasbro; Vimeo; Peloton Interactive; Zoominfo Technologies; Cineverse |
| BoW nouns / (m_i m_j) | Gaia; Curiositystream; Chicken Soup For The Soul E…; Coupang; Cineverse; Roku; Motorsport Games; Unity Software; U.S. Goldmining; Foot Locker |
| BoW nouns − (m_i+m_j)/2 | Gaia; Curiositystream; Roku; Chicken Soup For The Soul E…; Buzzfeed; Cineverse; Vimeo; Peloton Interactive; Hasbro; Coupang |
| BoW nouns − m_i m_j/med(m) | Gaia; Curiositystream; Chicken Soup For The Soul E…; Roku; Buzzfeed; Cineverse; Vimeo; Coupang; Peloton Interactive; Motorsport Games |

**Overlap of top-10 lists (out of 10; TNIC counts are aggregates)**

| ticker | dense∩bow | dense∩tnic | bow∩tnic | mult∩tnic | add∩tnic | null∩tnic | bow∩null | bow∩mult |
|---|---|---|---|---|---|---|---|---|
| AAPL | 0 | 0 | 2 | 1 | 3 | 3 | 8 | 2 |
| MSFT | 1 | 0 | 4 | 2 | 6 | 7 | 6 | 1 |
| NVDA | 0 | 0 | 3 | 2 | 4 | 4 | 7 | 2 |
| JPM | 1 | 2 | 7 | 2 | 8 | 8 | 9 | 1 |
| GS | 0 | 0 | 7 | 2 | 7 | 7 | 7 | 0 |
| JNJ | 2 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| PFE | 1 | 1 | 4 | 0 | 3 | 1 | 4 | 1 |
| KO | 6 | 4 | 7 | 5 | 7 | 7 | 9 | 7 |
| WMT | 2 | 1 | 6 | 3 | 6 | 6 | 9 | 5 |
| HD | 2 | 2 | 4 | 2 | 4 | 3 | 6 | 2 |
| BA | 3 | 3 | 7 | 4 | 7 | 6 | 8 | 3 |
| DAL | 4 | 3 | 9 | 6 | 9 | 9 | 10 | 6 |
| TSLA | 3 | 4 | 8 | 4 | 7 | 7 | 6 | 3 |
| NFLX | 3 | 1 | 1 | 1 | 1 | 1 | 8 | 5 |
