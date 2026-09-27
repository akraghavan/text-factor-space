"""Geographic words dropped from the bag-of-words vocabulary (SPEC §5; Hoberg-Phillips drop geographic terms so that
firms are not linked merely by where they operate). Single lower-case tokens: US states, countries and territories,
large US and world cities, regions and demonyms. Tokens that are generic English on their own (new, north, south, west,
united, states, city, island, cape, san, santa, costa, sierra, latin, ...) are deliberately left out."""
US_STATES = """alabama alaska arizona arkansas california colorado connecticut delaware florida georgia hawaii idaho illinois
indiana iowa kansas kentucky louisiana maine maryland massachusetts michigan minnesota mississippi missouri montana nebraska
nevada hampshire jersey mexico york carolina dakota ohio oklahoma oregon pennsylvania rhode tennessee texas utah vermont
virginia washington wisconsin wyoming columbia""".split()
COUNTRIES = """afghanistan albania algeria andorra angola antigua argentina armenia australia austria azerbaijan bahamas bahrain
bangladesh barbados belarus belgium belize benin bhutan bolivia bosnia herzegovina botswana brazil brunei bulgaria burkina faso
burundi cambodia cameroon canada chad chile china colombia comoros congo rica croatia cuba cyprus czech czechia denmark djibouti
dominica dominican ecuador egypt salvador eritrea estonia eswatini ethiopia fiji finland france gabon gambia germany ghana greece
grenada guatemala guinea guyana haiti honduras hungary iceland india indonesia iran iraq ireland israel italy jamaica japan jordan
kazakhstan kenya kiribati korea kosovo kuwait kyrgyzstan laos latvia lebanon lesotho liberia libya liechtenstein lithuania
luxembourg madagascar malawi malaysia maldives mali malta mauritania mauritius micronesia moldova monaco mongolia montenegro
morocco mozambique myanmar namibia nauru nepal netherlands zealand nicaragua niger nigeria macedonia norway oman pakistan palau
palestine panama papua paraguay peru philippines poland portugal qatar romania russia rwanda samoa marino arabia senegal serbia
seychelles leone singapore slovakia slovenia somalia sudan spain lanka suriname sweden switzerland syria taiwan tajikistan
tanzania thailand timor togo tonga trinidad tobago tunisia turkey turkmenistan tuvalu uganda ukraine emirates uruguay uzbekistan
vanuatu vatican venezuela vietnam yemen zambia zimbabwe hong kong macau macao puerto rico guam bermuda cayman scotland england
wales britain""".split()
CITIES = """chicago houston phoenix philadelphia antonio diego dallas jacksonville columbus charlotte indianapolis seattle denver
boston nashville detroit portland memphis louisville baltimore milwaukee albuquerque tucson fresno sacramento atlanta omaha miami
oakland minneapolis tulsa cleveland wichita orleans tampa pittsburgh cincinnati orlando raleigh honolulu anchorage francisco
angeles vegas brooklyn manhattan stamford hartford london paris tokyo beijing shanghai shenzhen guangzhou mumbai bangalore
bengaluru delhi hyderabad toronto montreal vancouver calgary ontario quebec alberta sydney melbourne frankfurt munich zurich
geneva amsterdam dublin brussels madrid milan rome moscow seoul taipei dubai istanbul paulo janeiro aires bogota lima santiago
johannesburg cairo lagos nairobi jakarta manila bangkok hanoi lumpur osaka kyoto hamburg berlin vienna prague warsaw stockholm
oslo copenhagen helsinki lisbon barcelona edinburgh aviv haifa""".split()
REGIONS = """europe asia africa americas oceania emea apac asean caribbean scandinavia american european asian african canadian
mexican chinese japanese korean indian british german french italian spanish brazilian australian russian israeli swiss dutch
irish swedish norwegian danish finnish nordic scandinavian""".split()
GEO = frozenset(US_STATES + COUNTRIES + CITIES + REGIONS)
