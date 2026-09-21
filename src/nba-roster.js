/* ============================================================
   NBA 2026–27 roster — supplied by Tom (Sept 2026), merged with
   Code 7's earlier curated list for stars missing from it.
   Format per player:  Name|POS|PRICE   (POS = G/F/C)
   PRICE = tier letter (B 900k · C 720k · D 560k · E 420k · F 300k)
           or an exact price in $k (e.g. 1700).
   *Name = new to the team for 2026–27 (🆕 on Tom's list).
   Positions and price tiers are Code 7's own estimates.
   ============================================================ */
const NBA_TIERS = { B: 900, C: 720, D: 560, E: 420, F: 300 };
const NBA_ROSTER = {
  ATL: 'Keshon Gilbert|G|F; RayJ Dennis|G|F; Jalen Johnson|F|1100; Keaton Wallace|G|F; CJ McCollum|G|C; Gabe Vincent|G|E; *Kingston Flemings|G|D; Dyson Daniels|G|C; Luguentz Dort|F|D; Nickeil Alexander-Walker|G|C; Buddy Hield|G|E; Ryan Nembhard|G|E; Henri Veesaar|C|F; Tony Bradley|C|F; Asa Newell|F|E; Onyeka Okongwu|C|C; Mouhamed Gueye|F|F; *Zuby Ejiofor|F|F; Aaron Wiggins|G|E; Jalen Wilson|F|F; Corey Kispert|F|E; Jock Landale|C|E',
  BOS: '*Dillon Mitchell|F|E; Milos Uzan|G|F; Tucker DeVries|F|F; Jayson Tatum|F|1200; Mitchell Robinson|C|D; Paul George|F|C; Derrick White|G|B; Payton Pritchard|G|C; *Chris Cenac Jr.|F|E; Ron Harper Jr.|F|F; Devin Carter|G|E; Jordan Walsh|F|F; Hugo González|F|E; Sam Hauser|F|E; Max Shulga|G|F; Mike Conley|G|F; Luka Garza|C|F; Baylor Scheierman|G|F; Amari Williams|C|F',
  BKN: 'Josh Minott|F|F; *Mikel Brown Jr.|G|D; Danny Wolf|F|E; Drake Powell|G|E; Egor Dëmin|G|D; *Joshua Jefferson|F|E; Nolan Traore|G|E; Keon Ellis|G|E; Terance Mann|G|F; Grant Nelson|F|F; Michael Porter Jr.|F|B; Day\'Ron Sharpe|C|E; Moritz Wagner|C|F; Noah Clowney|F|E; Julius Randle|F|B; Chaney Johnson|F|F; *Tyler Bilodeau|F|F; Ben Saraf|G|F',
  CHA: 'Michael Ajayi|F|F; Kylan Boswell|G|F; Royce O\'Neale|F|E; Dorian Finney-Smith|F|F; Grant Williams|F|F; Coby White|G|C; Sion James|G|E; *Christian Anderson|G|E; Kon Knueppel|G|B; Grayson Allen|G|E; Dennis Schröder|G|E; Naz Reid|C|C; Ryan Kalkbrenner|C|E; Antonio Reeves|G|F; Moussa Diabaté|C|E; PJ Hall|F|F; Pat Connaughton|G|F; Bez Mbeng|G|F; *Hannes Steinbach|F|E',
  CHI: 'Tobe Awaka|F|F; Jaylin Sellers|G|F; Josh Giddey|G|B; *Dailyn Swain|F|E; Rob Dillingham|G|E; *Caleb Wilson|F|D; Nic Claxton|C|D; Leonard Miller|F|F; Zach Collins|C|F; Matas Buzelis|F|C; Norman Powell|G|C; Noa Essengue|F|E; Jalen Smith|C|E; Tre Jones|G|E; Isaac Okoro|G|F; Patrick Williams|F|E',
  CLE: 'James Harden|G|1000; Thomas Bryant|C|F; Evan Mobley|C|1050; Sam Merrill|G|E; Peyton Watson|F|D; Craig Porter Jr.|G|F; Riley Minix|F|F; *Meleek Thomas|G|E; Khalifa Diop|C|F; Jaylon Tyson|F|E; Tristan Enaruna|F|F; Tyrese Proctor|G|F; Jarrett Allen|C|C; Mario Hezonja|F|F; Nae\'Qwan Tomlin|F|F; Ernest Udeh Jr.|C|F; Donovan Mitchell|G|1200',
  DAL: 'Tarik Biberović|G|F; Vsevolod Ishchenko|F|F; Max Christie|G|E; John Poulakidas|G|F; Dereck Lively II|C|D; Naji Marshall|F|E; Dwight Powell|C|F; Marcus Sasser|G|F; Zaccharie Risacher|F|D; Kyrie Irving|G|B; Jett Howard|F|F; *Morez Johnson Jr.|F|E; Caleb Martin|F|F; Daniel Gafford|C|E; P.J. Washington|F|D; Moussa Cissé|C|F; Cooper Flagg|F|1000; *Tobi Lawal|F|F',
  DEN: '*Trevon Brazile|F|F; *Bryce Hopkins|F|F; Alpha Diallo|F|F; Christian Braun|G|D; Cam Whitmore|F|E; Curtis Jones|G|F; Julian Strawther|G|F; Tyus Jones|G|E; DeMar DeRozan|F|C; DaRon Holmes II|F|F; Nikola Jokić|C|1700; Lonnie Walker IV|G|F; Spencer Jones|F|F; Zeke Nnaji|F|F; Cameron Johnson|F|D; KJ Simpson|G|F; Jamal Murray|G|1000; Aaron Gordon|F|D; Marvin Bagley III|F|F',
  DET: '*Ugonna Onyenso|C|F; *Ebuka Okorie|G|F; Jalen Duren|C|C; Cade Cunningham|G|1300; Isaac Jones|F|F; Ronald Holland II|F|E; Paul Reed|C|F; Ausar Thompson|F|C; Isaiah Joe|G|E; Gary Harris|G|F; Taurean Prince|F|F; Wendell Moore Jr.|F|F; Elijah Harkless|G|F; Chaz Lanier|G|F; John Collins|F|D; Daniss Jenkins|G|F; Kevin Huerter|G|E; Javonte Green|F|F',
  GSW: 'Nick Boyd|G|F; Obi Agbim|G|F; Gary Payton II|G|F; *Yaxel Lendeborg|F|E; Brandin Podziemski|G|D; Will Richard|G|F; Moses Moody|G|E; Kristaps Porziņģis|C|C; De\'Anthony Melton|G|E; Jimmy Butler III|F|B; Brandon Williams|G|F; Gui Santos|F|F; LJ Cryer|G|F; Nate Williams|G|F; Al Horford|C|E; Dalen Terry|G|F; Alex Toohey|F|F; Draymond Green|F|D; *Lajae Jones|F|F',
  HOU: 'Sean Pedulla|G|F; Bruce Thornton|G|F; Rafael Castro|C|F; Quadir Copeland|G|F; Aaron Holiday|G|F; Amen Thompson|G|B; Julian Phillips|F|F; Fred VanVleet|G|D; Kevin Durant|F|1100; Jae\'Sean Tate|F|F; Jabari Smith Jr.|F|D; Steven Adams|C|E; Reed Sheppard|G|E; Tari Eason|F|D; Isaiah Crawford|F|F; Alperen Şengün|C|1150; Clint Capela|C|E; Bogdan Bogdanović|G|F; Jeff Green|F|F',
  IND: 'Keba Keita|F|F; Kowacie Reeves Jr.|G|F; Rienk Mast|F|F; Jalen Warley|G|F; Tyrese Haliburton|G|1050; Obi Toppin|F|E; Andrew Nembhard|G|D; Braden Smith|G|F; Jarace Walker|F|E; T.J. McConnell|G|E; Kelly Oubre Jr.|F|E; Johnny Furphy|F|F; Jalen Slawson|F|F; Larry Nance Jr.|F|F; Aaron Nesmith|F|E; Kobe Brown|F|F; Ben Sheppard|G|F; Quenton Jackson|G|F; Jay Huff|C|E',
  LAC: 'Norchad Omier|F|F; *Baba Miller|F|F; *Nick Martinelli|F|F; *Narcisse Ngoy|C|F; Bradley Beal|G|E; Gradey Dick|G|E; *Keaton Wagler|G|D; Max Strus|F|E; Brandon Ingram|F|B; Kobe Sanders|G|F; Derrick Jones Jr.|F|E; Kris Dunn|G|E; Yuki Kawamura|G|F; Darius Garland|G|C; Brook Lopez|C|E; TyTy Washington Jr.|G|F; Yanic Konan Niederhäuser|C|F; Jordan Miller|F|F; Johni Broome|C|F',
  LAL: 'Arthur Kaluma|F|F; Meechie Johnson|G|F; Chase Ross|G|F; Adou Thiero|F|F; Jarred Vanderbilt|F|F; Matisse Thybulle|F|F; Dalton Knecht|F|F; Quentin Grimes|G|E; Jaden Hardy|G|F; Bronny James|G|F; Collin Sexton|G|E; Ziaire Williams|F|F; Jake LaRavia|F|E; Walker Kessler|C|D; Austin Reaves|G|B; Chris Mañon|G|F; AK Okereke|F|F; *Cameron Carr|G|F; Sandro Mamukelashvili|C|F',
  MEM: 'Jahmai Mashack|G|F; *Richie Saunders|G|F; Jaylen Wells|F|E; Scotty Pippen Jr.|G|E; Ty Jerome|G|E; Walter Clayton Jr.|G|E; D\'Angelo Russell|G|E; Jerami Grant|F|E; Javon Small|G|F; Micah Peavy|G|F; Zach Edey|C|D; Olivier-Maxence Prosper|F|F; Quinten Post|C|F; Taylor Hendricks|F|F; Cedric Coward|F|E; Jordan Hawkins|G|F; Cam Spencer|G|F; Kris Murray|F|F',
  MIA: 'J\'Vonne Hadley|F|F; Simone Fontecchio|F|F; Davion Mitchell|G|E; Trevor Keels|G|F; *Ryan Conwell|G|F; Nikola Jović|F|E; Giannis Antetokounmpo|F|1500; Nick Richards|C|F; Pelle Larsson|G|F; Tim Hardaway Jr.|G|F; Klay Thompson|G|E',
  MIL: '*Malique Lewis|F|F; Jake Stephens|C|F; *Nate Ament|F|D; *Brayden Burries|G|D; Jericho Sims|C|F; Myles Turner|C|C; Gary Trent Jr.|G|F; Kevin Porter Jr.|G|D; Kam Jones|G|F; Caris LeVert|G|F; Kel\'el Ware|C|C; Tyler Herro|G|B; Ryan Rollins|G|E; Kyle Kuzma|F|E; John Butler Jr.|F|F; AJ Green|G|F; Ousmane Dieng|F|F; Bogoljub Marković|F|F; Pete Nance|F|F',
  MIN: 'Donte DiVincenzo|G|E; LaMelo Ball|G|1050; Jaden McDaniels|F|D; Terrence Shannon Jr.|G|F; Anthony Edwards|G|1300; Jaylen Clark|G|F; Bones Hyland|G|F; Cody Williams|F|F; Ayo Dosunmu|G|E; Zyon Pullin|G|F; Joan Beringer|C|F; Jonathan Kuminga|F|D; Enrique Freeman|F|F; Rudy Gobert|C|C; *Isaiah Evans|F|E; Trey Lyles|F|F; Rocco Zikarsky|C|F',
  NOP: 'Jeremiah Fears|G|D; Zion Williamson|F|B; Herbert Jones|F|E; Jordan Poole|G|E; Kobe Bufkin|G|F; Dejounte Murray|G|D; DeAndre Jordan|C|F; AJ Johnson|G|F; Malik Dia|F|F; Trendon Watford|F|F; Bennedict Mathurin|G|D; *Jaron Pierre Jr.|G|F; Bryce McGowens|G|F; Karlo Matković|C|F; Yves Missi|C|E; Derik Queen|C|D; Trey Murphy III|F|C; Caleb Houstan|F|F; Christian Koloko|C|F; Saddiq Bey|F|F',
  NYK: 'Jack Kayil|G|F; *Tyler Nickel|F|F; Andre Drummond|C|F; Jordan Clarkson|G|F; Miles McBride|G|E; Josh Hart|G|D; Pacôme Dadiet|F|F; Jose Alvarado|G|F; OG Anunoby|F|C; Kevin McCullar Jr.|G|F; James Wiseman|C|F',
  OKC: 'Josh Dix|G|F; Cristoph Tilly|F|F; Shai Gilgeous-Alexander|G|1600; Jared McCain|G|E; Jaylin Williams|F|F; Chet Holmgren|C|1000; Jalen Williams|F|1000; Alex Caruso|G|E; Thomas Sorber|C|F; Otega Oweh|G|F; *Bennett Stirtz|G|E; *Aday Mara|C|F; Cason Wallace|G|E; Brooks Barnhizer|G|F; Ajay Mitchell|G|E; Kenrich Williams|F|F; Nikola Topić|G|F; Isaiah Hartenstein|C|D',
  ORL: 'Anthony Black|G|E; Jonathan Isaac|F|F; Jevon Carter|G|F; Desmond Bane|G|C; Jalen Suggs|G|D; JD Davison|G|F; Paolo Banchero|F|1100; Jamal Cain|F|F; Nikola Vučević|C|D; Jase Richardson|G|F; Malaki Branham|G|F; Colin Castleton|C|F; Franz Wagner|F|950; Tristan da Silva|F|F; Izaiyah Nelson|F|F; Alex Morales|G|F; Wendell Carter Jr.|C|E; Goga Bitadze|C|F; Noah Penda|F|F',
  PHI: 'Jameer Nelson Jr.|G|F; Saint Thomas|F|F; Duke Miles|G|F; *Labaron Philon|G|E; Dillon Jones|F|F; Tyrese Maxey|G|1150; Caleb Love|G|F; Kentavious Caldwell-Pope|G|F; Kyle Lowry|G|F; Jaylen Brown|F|1150; Justin Edwards|F|F; MarJon Beauchamp|F|F; Rayan Rupert|G|F; Joel Embiid|C|B; Anfernee Simons|G|D; LeBron James|F|1050; Tyrese Martin|G|F; Dominick Barlow|F|F; Adem Bona|C|F',
  PHX: 'Miles Bridges|F|D; Ryan Dunn|F|F; Amir Coffey|F|F; Dillon Brooks|F|E; Jalen Green|G|C; Haywood Highsmith|F|F; Luke Kennard|G|F; Khaman Maluach|C|E; Oso Ighodaro|C|F; Collin Gillespie|G|E; Koby Brea|G|F; Mark Williams|C|D; Devin Booker|G|1150; Jamaree Bouyea|G|F',
  POR: 'Jayson Kent|F|F; Damian Lillard|G|C; Scoot Henderson|G|E; Blake Wesley|G|F; Chris Youngblood|G|F; Jrue Holiday|G|E; Deni Avdija|F|B; John Tonje|G|F; Micah Potter|F|F; Ja Morant|G|1000; Branden Carlson|C|F; Yang Hansen|C|F; Shaedon Sharpe|G|D; Jeremy Sochan|F|F; Donovan Clingan|C|D; Vít Krejčí|G|F; Toumani Camara|F|E; Robert Williams III|C|F; Sidy Cissoko|G|F',
  SAC: 'Malik Monk|G|E; Jonathan Mogbo|F|F; Elfrid Payton|G|F; *Darius Acuff Jr.|G|D; Zach LaVine|G|C; Precious Achiuwa|F|F; Nique Clifford|G|F; Domantas Sabonis|C|B; Keegan Murray|F|D; Adam Flagler|G|F; De\'Andre Hunter|F|E; Ben Simmons|G|F; Daeqwon Plowden|G|F; Dylan Cardwell|C|F; *Alex Karaban|F|F; *Emanuel Sharp|G|F; Maxime Raynaud|C|F',
  SAS: 'Jayden Nunn|G|F; Ja\'Kobi Gillespie|G|F; Maliq Brown|F|F; Jordan McLaughlin|G|F; Victor Wembanyama|C|1600; Dylan Harper|G|C; Keldon Johnson|F|E; De\'Aaron Fox|G|B; Taelon Peter|G|F; Stephon Castle|G|C; Luke Kornet|C|F; *Tarris Reed Jr.|C|F; Carter Bryant|F|F; *Jayden Quaintance|F|E; Tobias Harris|F|E; Devin Vassell|G|E; David Jones Garcia|F|F; Julian Champagnie|F|E; Harrison Barnes|F|F',
  TOR: 'Nate Bittle|C|F; Jaden Bradley|G|F; A.J. Lawson|G|F; Kawhi Leonard|F|B; Scottie Barnes|F|1000; Immanuel Quickley|G|D; RJ Barrett|F|D; Kyle Anderson|F|F; Ja\'Kobe Walter|G|F; Malachi Smith|G|F; Jakob Poeltl|C|D',
  UTA: 'Hayden Gray|G|F; Kyle Filipowski|F|E; Blake Hinson|F|F; Svi Mykhailiuk|F|F; Jaxson Hayes|C|F; Mo Bamba|C|F; Ace Bailey|F|D; Jaren Jackson Jr.|F|B; Josh Okogie|G|F; *Darryn Peterson|G|750; Lauri Markkanen|F|B; Trey Alexander|G|F; Brice Sensabaugh|F|F; Jusuf Nurkić|C|E; Kevin Love|F|F; Harrison Ingram|F|F',
  WAS: 'KeShawn Murphy|F|F; Felix Okpara|C|F; Tre Johnson|G|E; Sharife Cooper|G|F; Anthony Gill|F|F; Kyshawn George|F|E; Khris Middleton|F|F; Alex Sarr|C|D; Tre Mann|G|F; Anthony Davis|C|B; Will Riley|F|F'
};
/* Stars from Code 7's earlier verified list that are NOT on Tom's list — kept so they're still draftable.
   Tom: confirm or delete these (see README). */
const NBA_KEEP = 'LAL:Luka Dončić|G|1550; NYK:Jalen Brunson|G|1250; NYK:Karl-Anthony Towns|C|1200; GSW:Stephen Curry|G|1100; WAS:Trae Young|G|1050; WAS:*AJ Dybantsa|F|800; MEM:*Cameron Boozer|F|750; MIA:Bam Adebayo|C|950';

function nbaReal() {
  const out = []; const seen = new Set();
  const add = (team, entry) => {
    let [name, pos, tier] = entry.split('|').map(s => s.trim());
    const isNew = name.startsWith('*'); if (isNew) name = name.slice(1);
    if (seen.has(name)) return; seen.add(name);
    const k = NBA_TIERS[tier] != null ? NBA_TIERS[tier] : +tier;
    // small deterministic spread inside a tier so equal-tier players aren't identical
    let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0;
    const jitter = NBA_TIERS[tier] != null ? 1 + ((h % 17) - 8) / 100 : 1;
    out.push([name, pos, team, Math.max(280000, Math.round(k * jitter) * 1000), isNew]);
  };
  for (const team of Object.keys(NBA_ROSTER)) NBA_ROSTER[team].split(';').forEach(e => e.trim() && add(team, e));
  NBA_KEEP.split(';').forEach(e => { const [team, rest] = e.trim().split(':'); add(team, rest); });
  return out;
}
