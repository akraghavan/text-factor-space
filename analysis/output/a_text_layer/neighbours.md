# Top-10 text neighbours, formation 2024-07-01

Text-only networks built from public SEC 10-K text; names from SEC EDGAR. Dense = centred bge-small cosine; BoW nouns = binary noun/proper-noun vectors (vocabulary from the prior 12 months). The version with TNIC-3 peers and SIC-3 marks (firm-level TNIC/CRSP data, SPEC §2) stays local: neighbours_full.md.

**AAPL** — Apple

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Jamf Holding; Emerson Radio; Grocery Outlet Holding; Gamestop; Amazon Com; Digital Turbine; Best Buy; Socket Mobile; Verizon Communications; Steven Madden |
| BoW nouns | Sonos; Arlo Technologies; Harmonic; Voxx International; Microsoft; Roku; Gopro; Electronic Arts; Take Two Interactive Softwa…; Corsair Gaming |

**MSFT** — Microsoft

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Unisys; Uipath; Rackspace Technology; Zoom Communications; Servicenow; Hewlett Packard Enterprise; Dell Technologies; Workday; Epam Systems; Digitalocean Holdings |
| BoW nouns | Adobe; Palo Alto Networks; Nutanix; Hp; Servicenow; Jamf Holding; Crowdstrike Holdings; F5; Okta; Ansys |

**NVDA** — Nvidia

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Palantir Technologies; Gaxos.Ai; Altair Engineering; Unity Software; Innodata; Mongodb; Arista Networks; Dynatrace; Unisys; Veritone |
| BoW nouns | Qualcomm; Gsi Technology; Marvell Technology; Xperi; One Stop Systems; Ceva; Pixelworks; Arteris; Synopsys; Broadcom |

**JPM** — Jpmorgan Chase & Co

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Bank Of Hawaii; Umb Financial; Metropolitan Bank Holding; Fifth Third Bancorp; Goldman Sachs Group; Uscb Financial Holdings; Republic Bancorp; Franklin Financial Services; Penns Woods Bancorp; Home Bancorp |
| BoW nouns | Goldman Sachs Group; Northern Trust; Us Bancorp De; Huntington Bancshares; Wells Fargo & Company; Fifth Third Bancorp; Truist Financial; M&T Bank; State Street; Ally Financial |

**GS** — Goldman Sachs Group

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lazard; Jefferies Financial Group; Evercore; Stonex Group; Stepstone Group; Houlihan Lokey; Schwab Charles; Jpmorgan Chase & Co; Stifel Financial; Msci |
| BoW nouns | Us Bancorp De; M&T Bank; Northern Trust; Ally Financial; State Street; Hancock Whitney; Fnb; Fifth Third Bancorp; Jpmorgan Chase & Co; Cf Bankshares |

**JNJ** — Johnson & Johnson

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Eli Lilly & Co; Gilead Sciences; Assertio Holdings; Abbvie; Supernus Pharmaceuticals; Organon & Co; Vanda Pharmaceuticals; Koru Medical Systems; Viridian Therapeutics, Inc.…; Neumora Therapeutics |
| BoW nouns | Abbvie; Regeneron Pharmaceuticals; Merck & Co; Eli Lilly & Co; Blueprint Medicines; Ironwood Pharmaceuticals; Esperion Therapeutics; Chrome Holding; Resmed; Bioxcel Therapeutics |

**PFE** — Pfizer

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Sarepta Therapeutics; Pliant Therapeutics; Globus Medical; Agenus; Mink Therapeutics; Leonabio; Integra Lifesciences Holdin…; Envista Holdings; Relay Therapeutics; Therapeuticsmd |
| BoW nouns | Leonabio; Kineta; Lineage Cell Therapeutics; Fractyl Health; Boston Scientific; Evoke Pharma; Janux Therapeutics; Bolt Biotherapeutics; Turnstone Biologics; Agenus |

**KO** — Coca Cola

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Coca-Cola Consolidated; Pepsico; Keurig Dr Pepper; Vita Coco Company; National Beverage; Molson Coors Beverage; Crown Holdings; Westrock Coffee; Pactiv Evergreen; Ecolab |
| BoW nouns | Pepsico; Celsius Holdings; Keurig Dr Pepper; Coca-Cola Consolidated; National Beverage; Zevia Pbc; Vita Coco Company; Mondelez International; Molson Coors Beverage; Boston Beer |

**WMT** — Walmart

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Boston Scientific; Steel Connect Llc; Aviat Networks; Freshpet; Thermo Fisher Scientific; Century Aluminum; Prestige Consumer Healthcare; Rogers; Netapp; Bank Of America |
| BoW nouns | Thermo Fisher Scientific; Autozone; Amplitude; Nu Skin Enterprises; Flywire; Paymentus Holdings; Premier; Scienture Holdings; Cognizant Technology Soluti…; European Wax Center |

**HD** — Home Depot

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lowes Companies; Green Brick Partners; Floor & Decor Holdings; American Woodmark; Wayfair; Target; Tri Pointe Homes; Legacy Housing; Bluelinx Holdings; Kb Home |
| BoW nouns | Lowes Companies; Ulta Beauty; Aaron'S Company; Etsy; Willscot Holdings; Destination Xl Group; Zillow Group; Ll Flooring Holdings; Floor & Decor Holdings; Tilly'S |

**BA** — Boeing

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Lockheed Martin; Spirit Aerosystems Holdings; General Dynamics; Barnes Group; Vse; Air Industries Group; Skywest; Transdigm Group; Sumisho Air Lease; Willis Lease Finance |
| BoW nouns | Rtx; Huntington Ingalls Industri…; Spirit Aerosystems Holdings; Hexcel; General Dynamics; Aerovironment; Triumph Group; Leidos Holdings; Kratos Defense & Security S…; Viasat |

**DAL** — Delta Air Lines

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Tutor Perini; Primerica; Clearone; Drilling Tools International; Effector Therapeutics; T Stamp; Profrac Holding; Confluent; Tyra Biosciences; Seaboard |
| BoW nouns | Tutor Perini; Healthcare Services Group; Primerica; Clearone; U.S. Goldmining; Rockwell Automation; Stryve Foods; Olaplex Holdings; Filana Therapeutics; Gevo |

**TSLA** — Tesla

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Phoenix Motor; Beam Global; Microvast Holdings; Azio Ai Holdings; Quantumscape; Expion Energy; Spruce Power Holding; Altus Power; Visteon; Nikola |
| BoW nouns | Canoo; Rivian Automotive, Inc. / De; Nikola; Lucid Group; Cenntro; Fluence Energy; Faraday Future Intelligent …; Forza X1; Hyzon Motors; Blink Charging |

**NFLX** — Netflix

| Network | Neighbours (most similar first) |
|---|---|
| Dense | Funko; Vimeo; Gaia; Gray Media; Cineverse; Amc Global Media; Take Two Interactive Softwa…; Amazon Com; Endeavor Group Holdings; Beasley Broadcast Group |
| BoW nouns | Gaia; Curiositystream; Roku; Buzzfeed; Vimeo; Chicken Soup For The Soul E…; Zoominfo Technologies; Peloton Interactive; Reservoir Media; Vizio Holding |

**Overlap of top-10 lists (out of 10; TNIC counts are aggregates)**

| ticker | dense∩bow | dense∩tnic | bow∩tnic |
|---|---|---|---|
| AAPL | 0 | 0 | 3 |
| MSFT | 1 | 1 | 4 |
| NVDA | 0 | 1 | 3 |
| JPM | 2 | 3 | 6 |
| GS | 1 | 1 | 7 |
| JNJ | 2 | 1 | 0 |
| PFE | 2 | 0 | 0 |
| KO | 6 | 4 | 6 |
| WMT | 1 | 0 | 0 |
| HD | 2 | 2 | 3 |
| BA | 2 | 3 | 5 |
| DAL | 3 | 0 | 0 |
| TSLA | 1 | 2 | 6 |
| NFLX | 2 | 1 | 1 |
