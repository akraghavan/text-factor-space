# Top-10 text neighbours, formation 2024-07-01

Text-only networks built from public SEC 10-K text; names from SEC EDGAR. Dense = centred bge-small cosine; BoW nouns = binary noun/proper-noun vectors (vocabulary from the prior 12 months). The version with TNIC-3 peers and SIC-3 marks (firm-level TNIC/CRSP data, SPEC §2) stays local: neighbours_full.md.

**AAPL** — Apple

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Jamf Holding; Emerson Radio; Grocery Outlet Holding; Gamestop; Amazon Com; Digital Turbine; Best Buy; Socket Mobile; Verizon Communications; Steven Madden |
| BoW nouns | Sonos; Arlo Technologies; Harmonic; Voxx International; Microsoft; Roku; Gopro; Electronic Arts; Take Two Interactive Softwa…; Corsair Gaming |
| BoW nouns / (m_i m_j) | Nike; Educational Development; Electronic Arts; Socket Mobile; Masco; Biolife Solutions; Weyco Group; Sherwin Williams; Digital Turbine; Escalade |
| BoW nouns − (m_i+m_j)/2 | Sonos; Arlo Technologies; Harmonic; Electronic Arts; Voxx International; Gopro; Take Two Interactive Softwa…; Roku; Corsair Gaming; Microsoft |
| BoW nouns − m_i m_j/med(m) | Sonos; Electronic Arts; Arlo Technologies; Harmonic; Voxx International; Gopro; Take Two Interactive Softwa…; Roku; Digital Turbine; Corsair Gaming |

**MSFT** — Microsoft

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Unisys; Uipath; Rackspace Technology; Zoom Communications; Servicenow; Hewlett Packard Enterprise; Dell Technologies; Workday; Epam Systems; Digitalocean Holdings |
| BoW nouns | Adobe; Palo Alto Networks; Nutanix; Hp; Servicenow; Jamf Holding; Crowdstrike Holdings; F5; Okta; Ansys |
| BoW nouns / (m_i m_j) | Unity Software; International Business Mach…; Usa Today; Electronic Arts; Dell Technologies; Cdw; Quantum; Ubiquiti; Educational Development; Inuvo |
| BoW nouns − (m_i+m_j)/2 | Adobe; Nutanix; Palo Alto Networks; Hp; Okta; Servicenow; Rackspace Technology; Jamf Holding; F5; Teradata |
| BoW nouns − m_i m_j/med(m) | Nutanix; Adobe; Rackspace Technology; Okta; Hp; Servicenow; Teradata; Salesforce; Electronic Arts; Roku |

**NVDA** — Nvidia

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Palantir Technologies; Gaxos.Ai; Unity Software; Altair Engineering; Innodata; Mongodb; Arista Networks; Dynatrace; Unisys; Veritone |
| BoW nouns | Qualcomm; Gsi Technology; Marvell Technology; Xperi; One Stop Systems; Ceva; Pixelworks; Arteris; Synopsys; Broadcom |
| BoW nouns / (m_i m_j) | Unity Software; Microchip Technology; Qualcomm; Chicago Rivet & Machine; International Business Mach…; Ceva; Dell Technologies; Lattice Semiconductor; Pixelworks; Magnachip Semiconductor |
| BoW nouns − (m_i+m_j)/2 | Qualcomm; Gsi Technology; Ceva; Marvell Technology; Pixelworks; Xperi; Lattice Semiconductor; One Stop Systems; Broadcom; Micron Technology |
| BoW nouns − m_i m_j/med(m) | Qualcomm; Gsi Technology; Ceva; Pixelworks; Marvell Technology; Lattice Semiconductor; Xperi; Micron Technology; Broadcom; Unity Software |

**JPM** — Jpmorgan Chase & Co

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Bank Of Hawaii; Umb Financial; Metropolitan Bank Holding; Fifth Third Bancorp; Goldman Sachs Group; Uscb Financial Holdings; Republic Bancorp; Franklin Financial Services; Penns Woods Bancorp; Home Bancorp |
| BoW nouns | Goldman Sachs Group; Northern Trust; Us Bancorp De; Huntington Bancshares; Wells Fargo & Company; Fifth Third Bancorp; Truist Financial; M&T Bank; State Street; Ally Financial |
| BoW nouns / (m_i m_j) | Oceanfirst Financial; Bank Of The James Financial…; Keycorp; Wells Fargo & Company; Bank Of New York Mellon; Macatawa Bank; S&T Bancorp; Umb Financial; Patriot National Bancorp; Arrow Financial |
| BoW nouns − (m_i+m_j)/2 | Northern Trust; Wells Fargo & Company; Us Bancorp De; Goldman Sachs Group; Huntington Bancshares; Fifth Third Bancorp; Truist Financial; M&T Bank; State Street; Bank Of Hawaii |
| BoW nouns − m_i m_j/med(m) | Wells Fargo & Company; Northern Trust; Us Bancorp De; Fifth Third Bancorp; Goldman Sachs Group; Huntington Bancshares; Truist Financial; Bank Of Hawaii; M&T Bank; Independent Bank Group |

**GS** — Goldman Sachs Group

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lazard; Jefferies Financial Group; Evercore; Stonex Group; Stepstone Group; Houlihan Lokey; Schwab Charles; Jpmorgan Chase & Co; Stifel Financial; Msci |
| BoW nouns | Us Bancorp De; M&T Bank; Northern Trust; Ally Financial; State Street; Hancock Whitney; Fnb; Fifth Third Bancorp; Jpmorgan Chase & Co; Cf Bankshares |
| BoW nouns / (m_i m_j) | Oceanfirst Financial; Macatawa Bank; Keycorp; S&T Bancorp; Pnc Financial Services Group; Arrow Financial; Wells Fargo & Company; Virginia National Bankshares; Central Plains Bancshares; Independent Bank |
| BoW nouns − (m_i+m_j)/2 | Us Bancorp De; M&T Bank; Northern Trust; State Street; Jpmorgan Chase & Co; Fifth Third Bancorp; Ally Financial; Hancock Whitney; Fnb; First Hawaiian |
| BoW nouns − m_i m_j/med(m) | Us Bancorp De; M&T Bank; Jpmorgan Chase & Co; Northern Trust; Fifth Third Bancorp; First Hawaiian; State Street; Old National Bancorp; Comerica; Pnc Financial Services Group |

**JNJ** — Johnson & Johnson

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Eli Lilly & Co; Gilead Sciences; Assertio Holdings; Abbvie; Supernus Pharmaceuticals; Organon & Co; Vanda Pharmaceuticals; Koru Medical Systems; Viridian Therapeutics, Inc.…; Neumora Therapeutics |
| BoW nouns | Abbvie; Regeneron Pharmaceuticals; Merck & Co; Eli Lilly & Co; Blueprint Medicines; Ironwood Pharmaceuticals; Esperion Therapeutics; Chrome Holding; Resmed; Bioxcel Therapeutics |
| BoW nouns / (m_i m_j) | Gilead Sciences; Supernus Pharmaceuticals; Cencora; Celldex Therapeutics; Abbott Laboratories; Sunshine Biopharma; Nektar Therapeutics; Xoma Royalty; Abbvie; Rocket One |
| BoW nouns − (m_i+m_j)/2 | Abbvie; Regeneron Pharmaceuticals; Merck & Co; Nektar Therapeutics; Eli Lilly & Co; Corcept Therapeutics; Ironwood Pharmaceuticals; Blueprint Medicines; Gilead Sciences; Evolus |
| BoW nouns − m_i m_j/med(m) | Abbvie; Nektar Therapeutics; Regeneron Pharmaceuticals; Gilead Sciences; Merck & Co; Corcept Therapeutics; Eli Lilly & Co; Ironwood Pharmaceuticals; Organon & Co; Cerevel Therapeutics Holdin… |

**PFE** — Pfizer

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Sarepta Therapeutics; Pliant Therapeutics; Globus Medical; Agenus; Mink Therapeutics; Leonabio; Integra Lifesciences Holdin…; Envista Holdings; Relay Therapeutics; Therapeuticsmd |
| BoW nouns | Leonabio; Kineta; Lineage Cell Therapeutics; Fractyl Health; Boston Scientific; Evoke Pharma; Janux Therapeutics; Bolt Biotherapeutics; Turnstone Biologics; Agenus |
| BoW nouns / (m_i m_j) | Cocrystal Pharma; Celldex Therapeutics; Supernus Pharmaceuticals; Stryve Foods; Westwood Holdings Group; Sunshine Biopharma; Rockwell Automation; Mays J W; Pulmatrix; Gilead Sciences |
| BoW nouns − (m_i+m_j)/2 | Leonabio; Boston Scientific; Lineage Cell Therapeutics; Fractyl Health; Kineta; Ensysce Biosciences; Evoke Pharma; Pliant Therapeutics; Agenus; Integra Lifesciences Holdin… |
| BoW nouns − m_i m_j/med(m) | Boston Scientific; Leonabio; Lineage Cell Therapeutics; Fractyl Health; Integra Lifesciences Holdin…; Ensysce Biosciences; Evoke Pharma; Pliant Therapeutics; Tevogen; Ernexa Therapeutics |

**KO** — Coca Cola

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Coca-Cola Consolidated; Pepsico; Keurig Dr Pepper; Vita Coco Company; National Beverage; Molson Coors Beverage; Crown Holdings; Westrock Coffee; Pactiv Evergreen; Ecolab |
| BoW nouns | Pepsico; Celsius Holdings; Keurig Dr Pepper; Coca-Cola Consolidated; National Beverage; Zevia Pbc; Vita Coco Company; Mondelez International; Molson Coors Beverage; Boston Beer |
| BoW nouns / (m_i m_j) | Coca-Cola Consolidated; Pepsico; Brown Forman; Celsius Holdings; Keurig Dr Pepper; Barfresh Food Group; National Beverage; Berry Global Group; Treehouse Foods; Vita Coco Company |
| BoW nouns − (m_i+m_j)/2 | Pepsico; Coca-Cola Consolidated; Celsius Holdings; Keurig Dr Pepper; National Beverage; Zevia Pbc; Vita Coco Company; Mondelez International; Molson Coors Beverage; Boston Beer |
| BoW nouns − m_i m_j/med(m) | Pepsico; Coca-Cola Consolidated; Celsius Holdings; Keurig Dr Pepper; National Beverage; Vita Coco Company; Zevia Pbc; Mondelez International; Molson Coors Beverage; Boston Beer |

**WMT** — Walmart

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Boston Scientific; Steel Connect Llc; Aviat Networks; Freshpet; Thermo Fisher Scientific; Century Aluminum; Prestige Consumer Healthcare; Rogers; Netapp; Bank Of America |
| BoW nouns | Thermo Fisher Scientific; Autozone; Amplitude; Nu Skin Enterprises; Flywire; Paymentus Holdings; Premier; Scienture Holdings; Cognizant Technology Soluti…; European Wax Center |
| BoW nouns / (m_i m_j) | Mastercard; Cognizant Technology Soluti…; Rockwell Automation; Autozone; Owens Corning; Timberland Bancorp; Thermo Fisher Scientific; Cencora; Cullen/Frost Bankers; Myr Group |
| BoW nouns − (m_i+m_j)/2 | Autozone; Thermo Fisher Scientific; Cognizant Technology Soluti…; Amplitude; Nu Skin Enterprises; Premier; Scienture Holdings; Aviat Networks; Paymentus Holdings; Leonabio |
| BoW nouns − m_i m_j/med(m) | Autozone; Thermo Fisher Scientific; Cognizant Technology Soluti…; Scienture Holdings; Premier; Myr Group; Aviat Networks; Amplitude; Mercadolibre; Nu Skin Enterprises |

**HD** — Home Depot

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lowes Companies; Green Brick Partners; Floor & Decor Holdings; American Woodmark; Wayfair; Target; Tri Pointe Homes; Legacy Housing; Bluelinx Holdings; Kb Home |
| BoW nouns | Lowes Companies; Ulta Beauty; Aaron'S Company; Etsy; Willscot Holdings; Destination Xl Group; Zillow Group; Ll Flooring Holdings; Floor & Decor Holdings; Tilly'S |
| BoW nouns / (m_i m_j) | Advance Auto Parts; Lowes Companies; Masco; Albertsons Companies; Tile Shop Holdings; W.W. Grainger; Bank Of The James Financial…; Dillard'S; Kohls; Floor & Decor Holdings |
| BoW nouns − (m_i+m_j)/2 | Lowes Companies; Ulta Beauty; Aaron'S Company; Floor & Decor Holdings; Destination Xl Group; Zillow Group; Ll Flooring Holdings; Tilly'S; O Reilly Automotive; Container Store Group |
| BoW nouns − m_i m_j/med(m) | Lowes Companies; Ulta Beauty; Floor & Decor Holdings; Zillow Group; Destination Xl Group; Wayfair; Zumiez; Lululemon Athletica; Carters; Ll Flooring Holdings |

**BA** — Boeing

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lockheed Martin; Spirit Aerosystems Holdings; General Dynamics; Barnes Group; Vse; Air Industries Group; Skywest; Transdigm Group; Sumisho Air Lease; Willis Lease Finance |
| BoW nouns | Rtx; Huntington Ingalls Industri…; Spirit Aerosystems Holdings; Hexcel; General Dynamics; Aerovironment; Triumph Group; Leidos Holdings; Kratos Defense & Security S…; Viasat |
| BoW nouns / (m_i m_j) | Primerica; Mays J W; Clearone; Tutor Perini; Healthcare Services Group; Lockheed Martin; Gevo; Rockwell Automation; Oceanfirst Financial; Enova International |
| BoW nouns − (m_i+m_j)/2 | Rtx; Spirit Aerosystems Holdings; Huntington Ingalls Industri…; Hexcel; Triumph Group; General Dynamics; Woodward; Aerovironment; Aar; Leidos Holdings |
| BoW nouns − m_i m_j/med(m) | Rtx; Spirit Aerosystems Holdings; Huntington Ingalls Industri…; Triumph Group; Hexcel; Woodward; General Dynamics; Primerica; Aar; Leidos Holdings |

**DAL** — Delta Air Lines

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Tutor Perini; Primerica; Clearone; Drilling Tools International; Effector Therapeutics; T Stamp; Profrac Holding; Confluent; Tyra Biosciences; Seaboard |
| BoW nouns | Tutor Perini; Healthcare Services Group; Primerica; Clearone; U.S. Goldmining; Rockwell Automation; Stryve Foods; Olaplex Holdings; Filana Therapeutics; Gevo |
| BoW nouns / (m_i m_j) | Tutor Perini; U.S. Goldmining; Clearone; Primerica; Healthcare Services Group; Stryve Foods; Rockwell Automation; Aeva Technologies; Central Plains Bancshares; Dutch Bros |
| BoW nouns − (m_i+m_j)/2 | Tutor Perini; Healthcare Services Group; Primerica; Clearone; U.S. Goldmining; Rockwell Automation; Stryve Foods; Olaplex Holdings; Gevo; Filana Therapeutics |
| BoW nouns − m_i m_j/med(m) | Tutor Perini; Healthcare Services Group; Primerica; Clearone; U.S. Goldmining; Rockwell Automation; Stryve Foods; Olaplex Holdings; Gevo; Filana Therapeutics |

**TSLA** — Tesla

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Phoenix Motor; Beam Global; Microvast Holdings; Azio Ai Holdings; Quantumscape; Expion Energy; Spruce Power Holding; Altus Power; Visteon; Nikola |
| BoW nouns | Canoo; Rivian Automotive, Inc. / De; Nikola; Lucid Group; Cenntro; Fluence Energy; Faraday Future Intelligent …; Forza X1; Hyzon Motors; Blink Charging |
| BoW nouns / (m_i m_j) | Ford Motor; Phoenix Motor; Canoo; Penske Automotive Group; Rivian Automotive, Inc. / De; Eos Energy Enterprises; American Battery Technology; Lucid Group; Leggett & Platt; Lithia Motors |
| BoW nouns − (m_i+m_j)/2 | Canoo; Rivian Automotive, Inc. / De; Lucid Group; Nikola; Cenntro; Fluence Energy; Forza X1; Phoenix Motor; Blink Charging; Xos |
| BoW nouns − m_i m_j/med(m) | Canoo; Rivian Automotive, Inc. / De; Lucid Group; Phoenix Motor; Nikola; Cenntro; Fluence Energy; Xos; Bollinger Innovations; Blink Charging |

**NFLX** — Netflix

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Funko; Vimeo; Gaia; Gray Media; Cineverse; Amc Global Media; Take Two Interactive Softwa…; Amazon Com; Endeavor Group Holdings; Beasley Broadcast Group |
| BoW nouns | Gaia; Curiositystream; Roku; Buzzfeed; Vimeo; Chicken Soup For The Soul E…; Zoominfo Technologies; Peloton Interactive; Reservoir Media; Vizio Holding |
| BoW nouns / (m_i m_j) | Gaia; Hartford Insurance Group; Delta Air Lines; Chicken Soup For The Soul E…; Curiositystream; Mastercard; One Group Hospitality; Cineverse; Coupang; Tutor Perini |
| BoW nouns − (m_i+m_j)/2 | Gaia; Curiositystream; Roku; Chicken Soup For The Soul E…; Buzzfeed; Vimeo; Peloton Interactive; Zoominfo Technologies; Cineverse; Reservoir Media |
| BoW nouns − m_i m_j/med(m) | Gaia; Curiositystream; Roku; Chicken Soup For The Soul E…; Buzzfeed; Vimeo; Peloton Interactive; Cineverse; Zoominfo Technologies; Reservoir Media |

**Overlap of top-10 lists (out of 10; TNIC counts are aggregates)**

| ticker | dense∩bow | dense∩tnic | bow∩tnic | mult∩tnic | add∩tnic | null∩tnic | bow∩null | bow∩mult |
|---|---|---|---|---|---|---|---|---|
| AAPL | 0 | 0 | 3 | 0 | 3 | 3 | 9 | 1 |
| MSFT | 1 | 1 | 4 | 0 | 6 | 5 | 5 | 0 |
| NVDA | 0 | 1 | 3 | 2 | 5 | 5 | 7 | 3 |
| JPM | 2 | 3 | 6 | 2 | 7 | 7 | 8 | 1 |
| GS | 1 | 1 | 7 | 2 | 7 | 7 | 6 | 0 |
| JNJ | 2 | 1 | 0 | 0 | 0 | 0 | 5 | 1 |
| PFE | 2 | 0 | 0 | 0 | 0 | 0 | 5 | 0 |
| KO | 6 | 4 | 6 | 4 | 6 | 6 | 10 | 6 |
| WMT | 1 | 0 | 0 | 0 | 0 | 0 | 7 | 3 |
| HD | 2 | 2 | 3 | 1 | 3 | 3 | 6 | 2 |
| BA | 2 | 3 | 5 | 1 | 5 | 4 | 7 | 0 |
| DAL | 3 | 0 | 0 | 0 | 0 | 0 | 10 | 7 |
| TSLA | 1 | 2 | 6 | 4 | 5 | 6 | 7 | 3 |
| NFLX | 2 | 1 | 1 | 1 | 1 | 1 | 9 | 3 |
