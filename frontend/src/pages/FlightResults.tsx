import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Search, Filter, Plane, MapPin, DollarSign } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface FlightResult {
  id: number;
  airline: string;
  flight_number: string;
  is_shared_flight?: string;
  aircraft_type?: string;
  departure_date?: string;
  departure_time: string;
  departure_airport: string;
  departure_city?: string;
  arrival_time: string;
  arrival_airport: string;
  arrival_city?: string;
  flight_duration?: string;
  has_stopover?: string;
  stopover_city?: string;
  stopover_airport?: string;
  price: number;
  currency: string;
  cabin_class?: string;
  discount_rate?: string;
  original_price?: number;
  scrape_time: string;
  source: string;
  status: string;
  notes?: string;
}

interface FlightStatistics {
  total_flights: number;
  min_price: number;
  max_price: number;
  avg_price: number;
}

const FlightResults: React.FC = () => {
  const [flights, setFlights] = useState<FlightResult[]>([]);
  const [statistics, setStatistics] = useState<FlightStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useState({
    minPrice: '',
    maxPrice: '',
    airline: '',
    limit: 50
  });

  // 获取航班数据
  const fetchFlights = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchParams.minPrice) params.append('min_price', searchParams.minPrice);
      if (searchParams.maxPrice) params.append('max_price', searchParams.maxPrice);
      if (searchParams.airline) params.append('airline', searchParams.airline);
      params.append('limit', searchParams.limit.toString());

      const response = await apiFetch(`/api/flights?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setFlights(data);
      }
    } catch (error) {
      console.error('获取航班数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const response = await apiFetch('/api/flights/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  useEffect(() => {
    fetchFlights();
    fetchStatistics();
  }, []);

  const handleSearch = () => {
    fetchFlights();
  };

  const handleReset = () => {
    setSearchParams({
      minPrice: '',
      maxPrice: '',
      airline: '',
      limit: 50
    });
    fetchFlights();
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(price);
  };

  const formatTime = (time: string) => {
    return time;
  };

  // 机场代号到名称的转换
  const getAirportName = (code: string) => {
    const airportMap: { [key: string]: string } = {
      // 主要机场
      'PEK': '北京首都国际机场',
      'SHA': '上海虹桥国际机场',
      'PVG': '上海浦东国际机场',
      'CAN': '广州白云国际机场',
      'SZX': '深圳宝安国际机场',
      'CTU': '成都双流国际机场',
      'XIY': '西安咸阳国际机场',
      'KMG': '昆明长水国际机场',
      'HGH': '杭州萧山国际机场',
      'NKG': '南京禄口国际机场',
      'TSN': '天津滨海国际机场',
      'DLC': '大连周水子国际机场',
      'SJW': '石家庄正定国际机场',
      'TYN': '太原武宿国际机场',
      'HET': '呼和浩特白塔国际机场',
      'HRB': '哈尔滨太平国际机场',
      'CGQ': '长春龙嘉国际机场',
      'SHE': '沈阳桃仙国际机场',
      'URC': '乌鲁木齐地窝堡国际机场',
      'WUH': '武汉天河国际机场',
      'CSX': '长沙黄花国际机场',
      'NNG': '南宁吴圩国际机场',
      'HAK': '海口美兰国际机场',
      'SYX': '三亚凤凰国际机场',
      'XMN': '厦门高崎国际机场',
      'FOC': '福州长乐国际机场',
      'NGB': '宁波栎社国际机场',
      'WNZ': '温州龙湾国际机场',
      'TAO': '青岛胶东国际机场',
      'JIN': '济南遥墙国际机场',
      'CGO': '郑州新郑国际机场',
      'WUX': '无锡硕放国际机场',
      'LYA': '洛阳北郊机场',
      'YNT': '烟台蓬莱国际机场',
      'WEH': '威海大水泊国际机场',
      'TNA': '济南遥墙国际机场',
      'XUZ': '徐州观音国际机场',
      'LYG': '连云港白塔埠机场',
      'HFE': '合肥新桥国际机场',
      'WHU': '武汉天河国际机场',
      'CSX': '长沙黄花国际机场',
      'NNG': '南宁吴圩国际机场',
      'HAK': '海口美兰国际机场',
      'SYX': '三亚凤凰国际机场',
      'XMN': '厦门高崎国际机场',
      'FOC': '福州长乐国际机场',
      'NGB': '宁波栎社国际机场',
      'WNZ': '温州龙湾国际机场',
      'TAO': '青岛胶东国际机场',
      'JIN': '济南遥墙国际机场',
      'CGO': '郑州新郑国际机场',
      'WUX': '无锡硕放国际机场',
      'LYA': '洛阳北郊机场',
      'YNT': '烟台蓬莱国际机场',
      'WEH': '威海大水泊国际机场',
      'TNA': '济南遥墙国际机场',
      'XUZ': '徐州观音国际机场',
      'LYG': '连云港白塔埠机场',
      'HFE': '合肥新桥国际机场',
      // 常见代码映射
      'UTF': '乌鲁木齐地窝堡国际机场',
      'QAA': '北京首都国际机场',
      'AAB': '北京首都国际机场',
      'JRU': '上海虹桥国际机场',
      'CGJ': '上海浦东国际机场',
      'BKU': '广州白云国际机场',
      'DIR': '深圳宝安国际机场',
      'AAA': '成都双流国际机场',
      'AAS': '西安咸阳国际机场',
      'UVO': '昆明长水国际机场'
    };
    return airportMap[code] || `${code}机场`;
  };

  // 计算飞行时长
  const calculateFlightDuration = (departureTime: string, arrivalTime: string) => {
    try {
      const [depHour, depMin] = departureTime.split(':').map(Number);
      const [arrHour, arrMin] = arrivalTime.split(':').map(Number);
      
      let depMinutes = depHour * 60 + depMin;
      let arrMinutes = arrHour * 60 + arrMin;
      
      // 处理跨天情况
      if (arrMinutes < depMinutes) {
        arrMinutes += 24 * 60;
      }
      
      const durationMinutes = arrMinutes - depMinutes;
      const hours = Math.floor(durationMinutes / 60);
      const minutes = durationMinutes % 60;
      
      return `${hours}h${minutes}m`;
    } catch (error) {
      return '';
    }
  };

  const getAirlineColor = (airline: string) => {
    const colors = {
      '中国国际航空': 'bg-blue-100 text-blue-800',
      '中国东方航空': 'bg-red-100 text-red-800',
      '中国南方航空': 'bg-green-100 text-green-800',
      '海南航空': 'bg-purple-100 text-purple-800',
      '四川航空': 'bg-orange-100 text-orange-800',
      '春秋航空': 'bg-pink-100 text-pink-800',
      '首都航空': 'bg-indigo-100 text-indigo-800',
      '吉祥航空': 'bg-yellow-100 text-yellow-800'
    };
    return colors[airline as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">航班查询结果</h1>
        <p className="text-gray-600">实时航班信息，按价格从低到高排列</p>
      </div>

      {/* 统计信息 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Plane className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">总航班数</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.total_flights}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">最低价格</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPrice(statistics.min_price)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">最高价格</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPrice(statistics.max_price)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">平均价格</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPrice(statistics.avg_price)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 搜索筛选 */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            搜索筛选
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="minPrice">最低价格</Label>
              <Input
                id="minPrice"
                type="number"
                placeholder="0"
                value={searchParams.minPrice}
                onChange={(e) => setSearchParams({...searchParams, minPrice: e.target.value})}
              />
            </div>
            
            <div>
              <Label htmlFor="maxPrice">最高价格</Label>
              <Input
                id="maxPrice"
                type="number"
                placeholder="10000"
                value={searchParams.maxPrice}
                onChange={(e) => setSearchParams({...searchParams, maxPrice: e.target.value})}
              />
            </div>
            
            <div>
              <Label htmlFor="airline">航空公司</Label>
              <Input
                id="airline"
                placeholder="输入航空公司"
                value={searchParams.airline}
                onChange={(e) => setSearchParams({...searchParams, airline: e.target.value})}
              />
            </div>
            
            <div>
              <Label htmlFor="limit">显示数量</Label>
              <Select
                value={searchParams.limit.toString()}
                onValueChange={(value: string) => setSearchParams({...searchParams, limit: parseInt(value)})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                  <SelectItem value="200">200</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex gap-2 mt-4">
            <Button onClick={handleSearch} className="flex items-center">
              <Search className="h-4 w-4 mr-2" />
              搜索
            </Button>
            <Button variant="outline" onClick={handleReset}>
              重置
            </Button>
            <Button variant="outline" onClick={fetchFlights} className="flex items-center">
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 航班列表 */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">加载中...</p>
          </div>
        ) : flights.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Plane className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">暂无航班数据</p>
            </CardContent>
          </Card>
        ) : (
          flights.map((flight) => (
            <Card key={flight.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                {/* 航班头部信息 */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <Badge className={`${getAirlineColor(flight.airline)} text-sm px-3 py-1`}>
                      {flight.airline}
                    </Badge>
                    <div className="flex items-center space-x-2">
                      <span className="text-lg font-mono font-bold">{flight.flight_number}</span>
                      {flight.is_shared_flight === '是' && (
                        <Badge variant="outline" className="text-xs">共享航班</Badge>
                      )}
                    </div>
                    {flight.aircraft_type && (
                      <span className="text-sm text-gray-600">机型: {flight.aircraft_type}</span>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-green-600">
                      {formatPrice(flight.price)}
                    </p>
                    {flight.original_price && flight.original_price > flight.price && (
                      <p className="text-sm text-gray-500 line-through">
                        原价: {formatPrice(flight.original_price)}
                      </p>
                    )}
                    {flight.discount_rate && (
                      <Badge variant="destructive" className="text-xs">
                        {flight.discount_rate}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* 航班路线信息 */}
                <div className="flex items-center justify-between mb-4">
                  <div className="text-center flex-1">
                    <div className="flex items-center justify-center text-gray-600 mb-1">
                      <MapPin className="h-4 w-4 mr-1" />
                      <span className="text-sm font-medium">
                        {flight.departure_city || getAirportName(flight.departure_airport)}
                      </span>
                    </div>
                    <p className="text-2xl font-bold">{formatTime(flight.departure_time)}</p>
                    <p className="text-xs text-gray-500">{getAirportName(flight.departure_airport)}</p>
                    {flight.departure_date && (
                      <p className="text-xs text-gray-500">{flight.departure_date}</p>
                    )}
                  </div>
                  
                  <div className="flex flex-col items-center mx-4">
                    <div className="w-20 h-px bg-gray-300"></div>
                    <Plane className="h-5 w-5 text-gray-400 my-2" />
                    <span className="text-sm text-gray-600 font-medium">
                      {flight.flight_duration || calculateFlightDuration(flight.departure_time, flight.arrival_time)}
                    </span>
                    {flight.has_stopover === '是' && (
                      <div className="text-xs text-orange-600 mt-1">
                        经停: {flight.stopover_city || flight.stopover_airport}
                      </div>
                    )}
                    <div className="w-20 h-px bg-gray-300"></div>
                  </div>
                  
                  <div className="text-center flex-1">
                    <div className="flex items-center justify-center text-gray-600 mb-1">
                      <MapPin className="h-4 w-4 mr-1" />
                      <span className="text-sm font-medium">
                        {flight.arrival_city || getAirportName(flight.arrival_airport)}
                      </span>
                    </div>
                    <p className="text-2xl font-bold">{formatTime(flight.arrival_time)}</p>
                    <p className="text-xs text-gray-500">{getAirportName(flight.arrival_airport)}</p>
                    {flight.departure_date && (
                      <p className="text-xs text-gray-500">{flight.departure_date}</p>
                    )}
                  </div>
                </div>

                {/* 航班详细信息 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">舱位等级</p>
                    <p className="text-sm font-medium">{flight.cabin_class || '经济舱'}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">飞行时长</p>
                    <p className="text-sm font-medium">
                      {flight.flight_duration || calculateFlightDuration(flight.departure_time, flight.arrival_time)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">是否经停</p>
                    <p className="text-sm font-medium">{flight.has_stopover || '否'}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">共享航班</p>
                    <p className="text-sm font-medium">{flight.is_shared_flight || '否'}</p>
                  </div>
                </div>
                
                {/* 任务时间信息 */}
                <div className="pt-4 border-t border-gray-100">
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>数据源: {flight.source}</span>
                    <span>抓取时间: {new Date(flight.scrape_time).toLocaleString('zh-CN')}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default FlightResults;
