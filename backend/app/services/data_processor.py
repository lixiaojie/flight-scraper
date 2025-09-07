"""
Data processing service for cleaning and normalizing flight data
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.flight_data import FlightData
from loguru import logger


class DataProcessor:
    """Service for processing and normalizing flight data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_flight_data(
        self, 
        raw_data: List[Dict[str, Any]], 
        task_id: int, 
        platform_name: str
    ) -> List[Dict[str, Any]]:
        """
        Process raw flight data and normalize it
        
        Args:
            raw_data: Raw flight data from scraping
            task_id: ID of the task
            platform_name: Name of the platform
            
        Returns:
            List of processed flight data dictionaries
        """
        processed_flights = []
        
        for flight in raw_data:
            try:
                processed_flight = self._normalize_flight_data(flight, task_id, platform_name)
                if processed_flight:
                    processed_flights.append(processed_flight)
            except Exception as e:
                logger.error(f"Error processing flight data: {str(e)}")
                continue
        
        logger.info(f"Processed {len(processed_flights)} flights from {len(raw_data)} raw entries")
        return processed_flights
    
    def _normalize_flight_data(
        self, 
        flight: Dict[str, Any], 
        task_id: int, 
        platform_name: str
    ) -> Optional[Dict[str, Any]]:
        """Normalize a single flight data entry"""
        try:
            # Extract and clean airline name
            airline = self._clean_airline_name(flight.get('airline', ''))
            if not airline:
                airline = self._extract_airline_from_flight_number(flight.get('flight_number', ''))
            
            # Extract and clean flight number
            flight_number = self._clean_flight_number(flight.get('flight_number', ''))
            
            # Parse and normalize times
            departure_time = self._parse_time(flight.get('departure_time', ''))
            arrival_time = self._parse_time(flight.get('arrival_time', ''))
            
            # Calculate duration if not provided
            duration = flight.get('duration')
            if not duration and departure_time and arrival_time:
                duration = self._calculate_duration(departure_time, arrival_time)
            
            # Clean and normalize price
            price = self._clean_price(flight.get('price'))
            if not price:
                return None  # Skip flights without valid price
            
            # Extract stops information
            stops = self._normalize_stops(flight.get('stops', 0))
            
            # Generate airports from cities (simplified)
            departure_airport = self._city_to_airport_code(flight.get('departure_city', ''))
            arrival_airport = self._city_to_airport_code(flight.get('arrival_city', ''))
            
            return {
                'task_id': task_id,
                'airline': airline,
                'flight_number': flight_number,
                'departure_airport': departure_airport,
                'arrival_airport': arrival_airport,
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'duration': duration,
                'price': price,
                'currency': 'USD',  # Default currency
                'stops': stops,
                'source_platform': platform_name,
                'scraped_at': datetime.utcnow(),
                'is_verified': False,
                'confidence_score': self._calculate_confidence_score(flight)
            }
            
        except Exception as e:
            logger.error(f"Error normalizing flight data: {str(e)}")
            return None
    
    def _clean_airline_name(self, airline: str) -> Optional[str]:
        """Clean and standardize airline name"""
        if not airline:
            return None
        
        # Remove extra whitespace and common suffixes
        airline = re.sub(r'\s+', ' ', airline.strip())
        airline = re.sub(r'\s+(Airlines?|Airways?|Airlines?|Inc\.?|Ltd\.?)$', '', airline, flags=re.IGNORECASE)
        
        # Common airline name mappings
        airline_mappings = {
            'united': 'United Airlines',
            'delta': 'Delta Air Lines',
            'american': 'American Airlines',
            'southwest': 'Southwest Airlines',
            'jetblue': 'JetBlue Airways',
            'alaska': 'Alaska Airlines',
            'spirit': 'Spirit Airlines',
            'frontier': 'Frontier Airlines',
            'allegiant': 'Allegiant Air',
            'hawaiian': 'Hawaiian Airlines'
        }
        
        airline_lower = airline.lower()
        for key, value in airline_mappings.items():
            if key in airline_lower:
                return value
        
        return airline.title() if airline else None
    
    def _extract_airline_from_flight_number(self, flight_number: str) -> Optional[str]:
        """Extract airline from flight number"""
        if not flight_number:
            return None
        
        # Common airline codes
        airline_codes = {
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'AA': 'American Airlines',
            'WN': 'Southwest Airlines',
            'B6': 'JetBlue Airways',
            'AS': 'Alaska Airlines',
            'NK': 'Spirit Airlines',
            'F9': 'Frontier Airlines',
            'G4': 'Allegiant Air',
            'HA': 'Hawaiian Airlines'
        }
        
        # Extract airline code (usually 2 letters at the beginning)
        match = re.match(r'^([A-Z]{2})', flight_number.upper())
        if match:
            code = match.group(1)
            return airline_codes.get(code)
        
        return None
    
    def _clean_flight_number(self, flight_number: str) -> Optional[str]:
        """Clean flight number"""
        if not flight_number:
            return None
        
        # Remove extra whitespace and common prefixes
        flight_number = re.sub(r'\s+', '', flight_number.strip())
        flight_number = re.sub(r'^(Flight|FL)\s*', '', flight_number, flags=re.IGNORECASE)
        
        return flight_number.upper() if flight_number else None
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string to datetime object"""
        if not time_str:
            return None
        
        # Common time formats
        time_formats = [
            '%H:%M',      # 14:30
            '%I:%M %p',   # 2:30 PM
            '%I:%M%p',    # 2:30PM
            '%H:%M:%S',   # 14:30:00
        ]
        
        for fmt in time_formats:
            try:
                # Use today's date as base
                today = datetime.now().date()
                time_obj = datetime.strptime(time_str.strip(), fmt).time()
                return datetime.combine(today, time_obj)
            except ValueError:
                continue
        
        # Try to extract time using regex
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', time_str.upper())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            ampm = time_match.group(3)
            
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
            
            today = datetime.now().date()
            return datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
        
        return None
    
    def _calculate_duration(self, departure: datetime, arrival: datetime) -> Optional[str]:
        """Calculate flight duration"""
        if not departure or not arrival:
            return None
        
        # Handle overnight flights
        if arrival < departure:
            arrival += timedelta(days=1)
        
        duration = arrival - departure
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        return f"{hours}h {minutes}m"
    
    def _clean_price(self, price: Any) -> Optional[float]:
        """Clean and normalize price"""
        if price is None:
            return None
        
        if isinstance(price, (int, float)):
            return float(price)
        
        if isinstance(price, str):
            # Remove currency symbols and commas
            price_str = re.sub(r'[^\d.,]', '', price)
            price_str = price_str.replace(',', '')
            
            try:
                return float(price_str)
            except ValueError:
                return None
        
        return None
    
    def _normalize_stops(self, stops: Any) -> int:
        """Normalize stops count"""
        if isinstance(stops, int):
            return max(0, stops)
        
        if isinstance(stops, str):
            stops_lower = stops.lower()
            if 'nonstop' in stops_lower or 'direct' in stops_lower:
                return 0
            elif '1' in stops_lower:
                return 1
            elif '2' in stops_lower:
                return 2
        
        return 0
    
    def _city_to_airport_code(self, city: str) -> str:
        """Convert city name to airport code (simplified mapping)"""
        if not city:
            return ''
        
        # Common city to airport mappings
        city_mappings = {
            'new york': 'JFK',
            'los angeles': 'LAX',
            'chicago': 'ORD',
            'houston': 'IAH',
            'phoenix': 'PHX',
            'philadelphia': 'PHL',
            'san antonio': 'SAT',
            'san diego': 'SAN',
            'dallas': 'DFW',
            'san jose': 'SJC',
            'austin': 'AUS',
            'jacksonville': 'JAX',
            'fort worth': 'DFW',
            'columbus': 'CMH',
            'charlotte': 'CLT',
            'seattle': 'SEA',
            'denver': 'DEN',
            'washington': 'DCA',
            'boston': 'BOS',
            'el paso': 'ELP',
            'nashville': 'BNA',
            'detroit': 'DTW',
            'oklahoma city': 'OKC',
            'portland': 'PDX',
            'las vegas': 'LAS',
            'memphis': 'MEM',
            'louisville': 'SDF',
            'baltimore': 'BWI',
            'milwaukee': 'MKE',
            'albuquerque': 'ABQ',
            'tucson': 'TUS',
            'fresno': 'FAT',
            'sacramento': 'SMF',
            'mesa': 'PHX',
            'kansas city': 'MCI',
            'atlanta': 'ATL',
            'long beach': 'LGB',
            'colorado springs': 'COS',
            'raleigh': 'RDU',
            'miami': 'MIA',
            'virginia beach': 'ORF',
            'omaha': 'OMA',
            'oakland': 'OAK',
            'minneapolis': 'MSP',
            'tulsa': 'TUL',
            'arlington': 'DFW',
            'tampa': 'TPA',
            'new orleans': 'MSY',
            'wichita': 'ICT',
            'cleveland': 'CLE',
            'bakersfield': 'BFL',
            'aurora': 'DEN',
            'anaheim': 'SNA',
            'honolulu': 'HNL',
            'santa ana': 'SNA',
            'corpus christi': 'CRP',
            'riverside': 'ONT',
            'lexington': 'LEX',
            'stockton': 'SCK',
            'toledo': 'TOL',
            'st. paul': 'MSP',
            'newark': 'EWR',
            'greensboro': 'GSO',
            'plano': 'DFW',
            'henderson': 'LAS',
            'lincoln': 'LNK',
            'buffalo': 'BUF',
            'jersey city': 'EWR',
            'chula vista': 'SAN',
            'fort wayne': 'FWA',
            'orlando': 'MCO',
            'st. petersburg': 'PIE',
            'chandler': 'PHX',
            'laredo': 'LRD',
            'norfolk': 'ORF',
            'durham': 'RDU',
            'madison': 'MSN',
            'lubbock': 'LBB',
            'irvine': 'SNA',
            'winston-salem': 'INT',
            'glendale': 'PHX',
            'garland': 'DFW',
            'hialeah': 'MIA',
            'reno': 'RNO',
            'chesapeake': 'ORF',
            'gilbert': 'PHX',
            'baton rouge': 'BTR',
            'irving': 'DFW',
            'scottsdale': 'PHX',
            'north las vegas': 'LAS',
            'fremont': 'SJC',
            'boise': 'BOI',
            'richmond': 'RIC',
            'san bernardino': 'ONT',
            'birmingham': 'BHM',
            'spokane': 'GEG',
            'rochester': 'ROC',
            'des moines': 'DSM',
            'modesto': 'MOD',
            'fayetteville': 'XNA',
            'tacoma': 'SEA',
            'oxnard': 'OXR',
            'fontana': 'ONT',
            'columbus': 'CMH',
            'montgomery': 'MGM',
            'moreno valley': 'ONT',
            'shreveport': 'SHV',
            'aurora': 'DEN',
            'yonkers': 'LGA',
            'akron': 'CAK',
            'huntington beach': 'SNA',
            'little rock': 'LIT',
            'augusta': 'AGS',
            'amarillo': 'AMA',
            'glendale': 'PHX',
            'mobile': 'MOB',
            'grand rapids': 'GRR',
            'salt lake city': 'SLC',
            'tallahassee': 'TLH',
            'huntsville': 'HSV',
            'grand prairie': 'DFW',
            'knoxville': 'TYS',
            'worcester': 'ORH',
            'newport news': 'ORF',
            'brownsville': 'BRO',
            'overland park': 'MCI',
            'santa clarita': 'BUR',
            'providence': 'PVD',
            'garden grove': 'SNA',
            'chattanooga': 'CHA',
            'oceanside': 'SAN',
            'jackson': 'JAN',
            'fort lauderdale': 'FLL',
            'santa rosa': 'STS',
            'rancho cucamonga': 'ONT',
            'port st. lucie': 'PBI',
            'tempe': 'PHX',
            'ontario': 'ONT',
            'vancouver': 'YVR',
            'sioux falls': 'FSD',
            'springfield': 'SGF',
            'peoria': 'PIA',
            'pembroke pines': 'FLL',
            'elk grove': 'SMF',
            'rockford': 'RFD',
            'palmdale': 'PMD',
            'corona': 'ONT',
            'salinas': 'SNS',
            'pomona': 'ONT',
            'pasadena': 'BUR',
            'joliet': 'ORD',
            'paterson': 'EWR',
            'kansas city': 'MCI',
            'torrance': 'LAX',
            'syracuse': 'SYR',
            'bridgeport': 'BDR',
            'hayward': 'OAK',
            'fort collins': 'FNL',
            'escondido': 'SAN',
            'lakewood': 'DEN',
            'hollywood': 'FLL',
            'dayton': 'DAY',
            'sunnyvale': 'SJC',
            'cary': 'RDU',
            'mesquite': 'DFW',
            'midland': 'MAF',
            'savannah': 'SAV',
            'clarksville': 'BNA',
            'orange': 'SNA',
            'pasadena': 'BUR',
            'fullerton': 'SNA',
            'killeen': 'GRK',
            'frisco': 'DFW',
            'hampton': 'ORF',
            'mcallen': 'MFE',
            'west valley city': 'SLC',
            'columbia': 'CAE',
            'olathe': 'MCI',
            'sterling heights': 'DTW',
            'new haven': 'HVN',
            'miramar': 'FLL',
            'waco': 'ACT',
            'thousand oaks': 'BUR',
            'cedar rapids': 'CID',
            'charleston': 'CHS',
            'visalia': 'VIS',
            'topeka': 'FOE',
            'elizabeth': 'EWR',
            'roseville': 'SMF',
            'carrollton': 'DFW',
            'coral springs': 'FLL',
            'sterling heights': 'DTW',
            'allen': 'DFW',
            'beaumont': 'BPT',
            'allentown': 'ABE',
            'sugar land': 'IAH',
            'abilene': 'ABI',
            'round rock': 'AUS',
            'college station': 'CLL',
            'pearland': 'IAH',
            'richardson': 'DFW',
            'odessa': 'MAF',
            'arvada': 'DEN',
            'ventura': 'OXR',
            'simi valley': 'BUR',
            'palmdale': 'PMD',
            'centennial': 'DEN',
            'boulder': 'WBU',
            'west covina': 'ONT',
            'brockton': 'BOS',
            'roanoke': 'ROA',
            'billings': 'BIL',
            'compton': 'LAX',
            'gainesville': 'GNV',
            'fairfield': 'SUI',
            'elgin': 'ORD',
            'richmond': 'RIC',
            'berkeley': 'OAK',
            'westminster': 'DEN',
            'carlsbad': 'SAN',
            'provo': 'PVU',
            'lowell': 'BOS',
            'antioch': 'OAK',
            'temecula': 'ONT',
            'norwalk': 'LAX',
            'daly city': 'SFO',
            'burbank': 'BUR',
            'santa clara': 'SJC',
            'el cajon': 'SAN',
            'san mateo': 'SFO',
            'clovis': 'FAT',
            'compton': 'LAX',
            'jurupa valley': 'ONT',
            'vista': 'SAN',
            'south gate': 'LAX',
            'mission viejo': 'SNA',
            'vacaville': 'SUI',
            'carson': 'LAX',
            'hesperia': 'ONT',
            'santa monica': 'LAX',
            'westminster': 'DEN',
            'redding': 'RDD',
            'santa barbara': 'SBA',
            'chico': 'CIC',
            'newport beach': 'SNA',
            'hawthorne': 'LAX',
            'citrus heights': 'SMF',
            'tracy': 'SCK',
            'alhambra': 'LAX',
            'livermore': 'OAK',
            'buena park': 'SNA',
            'lakewood': 'DEN',
            'merced': 'MCE',
            'hemet': 'ONT',
            'chino': 'ONT',
            'menifee': 'ONT',
            'chino hills': 'ONT',
            'redwood city': 'SFO',
            'lake forest': 'SNA',
            'napa': 'APC',
            'turlock': 'MOD',
            'madera': 'MAE',
            'mountain view': 'SJC',
            'alameda': 'OAK',
            'santa ana': 'SNA',
            'yuba city': 'MYV',
            'san rafael': 'STS',
            'pleasanton': 'OAK',
            'tulare': 'TLR',
            'cupertino': 'SJC',
            'morgan hill': 'SJC',
            'redondo beach': 'LAX',
            'san clemente': 'SNA',
            'san jacinto': 'ONT',
            'danville': 'OAK',
            'west sacramento': 'SMF',
            'san carlos': 'SFO',
            'san bruno': 'SFO',
            'san luis obispo': 'SBP',
            'san ramon': 'OAK',
            'los gatos': 'SJC',
            'san leandro': 'OAK',
            'foster city': 'SFO',
            'belmont': 'SFO',
            'san rafael': 'STS',
            'san mateo': 'SFO',
            'san bruno': 'SFO',
            'san carlos': 'SFO',
            'san leandro': 'OAK',
            'san ramon': 'OAK',
            'san luis obispo': 'SBP',
            'san clemente': 'SNA',
            'san jacinto': 'ONT',
            'san rafael': 'STS',
            'san mateo': 'SFO',
            'san bruno': 'SFO',
            'san carlos': 'SFO',
            'san leandro': 'OAK',
            'san ramon': 'OAK',
            'san luis obispo': 'SBP',
            'san clemente': 'SNA',
            'san jacinto': 'ONT'
        }
        
        city_lower = city.lower().strip()
        return city_mappings.get(city_lower, city.upper()[:3])
    
    def _calculate_confidence_score(self, flight: Dict[str, Any]) -> float:
        """Calculate confidence score for flight data quality"""
        score = 0.0
        max_score = 10.0
        
        # Price (2 points)
        if flight.get('price'):
            score += 2.0
        
        # Departure time (2 points)
        if flight.get('departure_time'):
            score += 2.0
        
        # Arrival time (2 points)
        if flight.get('arrival_time'):
            score += 2.0
        
        # Airline (1 point)
        if flight.get('airline'):
            score += 1.0
        
        # Flight number (1 point)
        if flight.get('flight_number'):
            score += 1.0
        
        # Duration (1 point)
        if flight.get('duration'):
            score += 1.0
        
        # Stops (1 point)
        if flight.get('stops') is not None:
            score += 1.0
        
        return min(score / max_score, 1.0)
