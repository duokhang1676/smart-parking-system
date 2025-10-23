import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/parking_service.dart';
import '../services/user_session.dart';
import '../services/api_service.dart';

class RegisterPage extends StatefulWidget {  
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  // Controllers for form fields
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _parkingNameController = TextEditingController();
  final TextEditingController _parkingAddressController = TextEditingController();
  final TextEditingController _licensePlateController = TextEditingController();
  final TextEditingController _vehicleMakeController = TextEditingController();
  final TextEditingController _vehicleColorController = TextEditingController();
  
  // User data
  String userId = "";
  String userName = "";
  String userPhoneNumber = "";
  
  // Search functionality
  List<Map<String, dynamic>> _allParkings = [];
  List<Map<String, dynamic>> _filteredParkings = [];
  bool _isSearching = false;
  bool _showSearchResults = false;
  
  // Selected parking info
  String _selectedParkingId = "";
  bool _isLoadingParkingId = false;
  
  // Registration state
  bool _isSubmittingRegistration = false;
  
  // Selected plan
  String? _selectedPlan;
  bool _acceptedTerms = false;

  @override
  void initState() {
    super.initState();
    _initializeUserData();
    _loadActiveParkings();
    _searchController.addListener(_onSearchChanged);
  }

  // Initialize user data from UserSession
  void _initializeUserData() async {
    final userSession = Provider.of<UserSession>(context, listen: false);
    
    if (userSession.isLoggedIn) {
      setState(() {
        userId = userSession.userId;
        userPhoneNumber = userSession.userPhone;
        userName = userSession.userName;
      });
      print('RegisterPage initialized with UserSession: userId=$userId, phone=$userPhoneNumber, name=$userName');
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _parkingNameController.dispose();
    _parkingAddressController.dispose();
    _licensePlateController.dispose();
    _vehicleMakeController.dispose();
    _vehicleColorController.dispose();
    super.dispose();
  }

  // Load all active parkings from API
  Future<void> _loadActiveParkings() async {
    try {
      final parkings = await ParkingService.getActiveParkings();
      setState(() {
        _allParkings = parkings;
        _filteredParkings = parkings;
      });
      print('Loaded ${parkings.length} active parkings');
    } catch (e) {
      print('Error loading parkings: $e');
      // Show error message to user
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to load parking locations'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // Filter parkings based on search text
  void _onSearchChanged() {
    final searchText = _searchController.text.toLowerCase();
    
    setState(() {
      if (searchText.isEmpty) {
        _filteredParkings = _allParkings;
        _showSearchResults = false;
      } else {
        _filteredParkings = _allParkings.where((parking) {
          final name = (parking['parking_name'] ?? '').toString().toLowerCase();
          final address = (parking['address'] ?? '').toString().toLowerCase();
          return name.contains(searchText) || address.contains(searchText);
        }).toList();
        _showSearchResults = true;
      }
    });
  }

  // Select a parking from search results
  void _selectParking(Map<String, dynamic> parking) async {
    final parkingName = parking['parking_name'] ?? '';
    final parkingAddress = parking['address'] ?? '';
    
    setState(() {
      _parkingNameController.text = parkingName;
      _parkingAddressController.text = parkingAddress;
      _searchController.clear();
      _showSearchResults = false;
      _isLoadingParkingId = true;
    });

    // Auto-fetch parking ID based on selected parking
    await _fetchParkingId(parkingAddress, parkingName);
  }

  // Fetch parking ID for the selected parking
  Future<void> _fetchParkingId(String address, String parkingName) async {
    try {
      print('Fetching parking ID for: $address, $parkingName');
      
      final parkingId = await ParkingService.getParkingId(address, parkingName);
      
      setState(() {
        _selectedParkingId = parkingId;
        _isLoadingParkingId = false;
      });
      
      print('Successfully fetched parking ID: $_selectedParkingId');
      
    } catch (e) {
      setState(() {
        _selectedParkingId = '';
        _isLoadingParkingId = false;
      });
      
      print('Failed to fetch parking ID: $e');
      
      // Show error message to user
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Unable to get parking information. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _appBar(),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        children: [
          SizedBox(height: 40),
          Text(
            'Monthly Parking',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          SizedBox(height: 10),
          Text(
            'Please fill the input below here',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey,
                ),
          ),
          _searchSection(),
          SizedBox(height: 40),
          _registerSection(context)
        ],
      )
    );
  }

  Container _registerSection(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Color(0xff1D1617).withValues(alpha: 0.08),
            spreadRadius: 0,
            blurRadius: 20,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Personal Information Section
          _buildSectionTitle('Personal Information', Icons.person),
          SizedBox(height: 16),
          
          TextField(
            controller: TextEditingController(text: userName),
            readOnly: true,
            decoration: InputDecoration(
              labelText: 'Full Name',
              prefixIcon: Icon(Icons.person_outline),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          SizedBox(height: 16),
          
          TextField(
            controller: TextEditingController(text: userPhoneNumber),
            readOnly: true,
            decoration: InputDecoration(
              labelText: 'Phone Number',
              prefixIcon: Icon(Icons.phone_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          // SizedBox(height: 16),
          
          // TextField(
          //   decoration: InputDecoration(
          //     labelText: 'Email Address',
          //     prefixIcon: Icon(Icons.email_outlined),
          //     border: OutlineInputBorder(
          //       borderRadius: BorderRadius.circular(12),
          //     ),
          //     filled: true,
          //     fillColor: Color(0xffF7F8F8),
          //   ),
          // ),
          
          SizedBox(height: 24),
          
          // Vehicle Information Section
          _buildSectionTitle('Vehicle Information', Icons.directions_car),
          SizedBox(height: 16),
          
          TextField(
            controller: _licensePlateController,
            decoration: InputDecoration(
              labelText: 'License Plate Number',
              prefixIcon: Icon(Icons.confirmation_number_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          SizedBox(height: 16),
          
          TextField(
            controller: _vehicleMakeController,
            decoration: InputDecoration(
              labelText: 'Vehicle Make & Model',
              prefixIcon: Icon(Icons.car_rental_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          SizedBox(height: 16),
          
          TextField(
            controller: _vehicleColorController,
            decoration: InputDecoration(
              labelText: 'Vehicle Color',
              prefixIcon: Icon(Icons.palette_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          
          SizedBox(height: 24),
          
          // Parking Details Section
          _buildSectionTitle('Parking Details', Icons.local_parking),
          SizedBox(height: 16),
          
          // TextField(
          //   readOnly: true,
          //   decoration: InputDecoration(
          //     labelText: 'Selected Parking Zone',
          //     prefixIcon: Icon(Icons.location_on_outlined),
          //     border: OutlineInputBorder(
          //       borderRadius: BorderRadius.circular(12),
          //     ),
          //     filled: true,
          //     fillColor: Colors.grey.shade100,
          //   ),
          // ),
          // SizedBox(height: 16),
          TextField(
            controller: _parkingNameController,
            readOnly: true,
            decoration: InputDecoration(
              labelText: 'Parking name',
              prefixIcon: Icon(Icons.location_searching_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          SizedBox(height: 16),
          TextField(
            controller: _parkingAddressController,
            readOnly: true,
            decoration: InputDecoration(
              labelText: 'Parking Address',
              prefixIcon: Icon(Icons.location_on_outlined),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Color(0xffF7F8F8),
            ),
          ),
          SizedBox(height: 16),
          
          // Subscription Plan Dropdown
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300),
              color: Color(0xffF7F8F8),
            ),
            child: DropdownButtonFormField<String>(
              isExpanded: true, // This ensures the dropdown takes full width
              value: _selectedPlan,
              decoration: InputDecoration(
                labelText: 'Monthly Plan',
                prefixIcon: Icon(Icons.calendar_month_outlined),
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              ),
              items: [
                DropdownMenuItem(
                  value: '1month', 
                  child: Text(
                    '1 Month - 1000VND',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 14),
                  ),
                ),
                DropdownMenuItem(
                  value: '3months', 
                  child: Text(
                    '3 Months - 2000VND (6% off)',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 14),
                  ),
                ),
                DropdownMenuItem(
                  value: '6months', 
                  child: Text(
                    '6 Months - 4000VND (10% off)',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 14),
                  ),
                ),
                DropdownMenuItem(
                  value: '12months', 
                  child: Text(
                    '12 Months - 5000VND (15% off)',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 14),
                  ),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedPlan = value;
                });
              },
            ),
          ),
          
          SizedBox(height: 24),
          // Terms and Conditions
          Row(
            children: [
              Checkbox(
                value: _acceptedTerms,
                onChanged: (value) {
                  setState(() {
                    _acceptedTerms = value ?? false;
                  });
                },
              ),
              Expanded(
                child: Text(
                  'I agree to the Terms & Conditions and Privacy Policy',
                  style: TextStyle(fontSize: 14),
                ),
              ),
            ],
          ),
          
          SizedBox(height: 30),
          
          // Register Button
          SizedBox(
            height: 56,
            child: ElevatedButton(
              onPressed: _isSubmittingRegistration ? null : _validateAndSubmit,
              style: ElevatedButton.styleFrom(
                backgroundColor: _isSubmittingRegistration ? Colors.grey.shade400 : Colors.blue.shade600,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 2,
              ),
              child: _isSubmittingRegistration
                ? Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      ),
                      SizedBox(width: 12),
                      Text(
                        'Đang đăng ký...',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  )
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.app_registration, color: Colors.white),
                      SizedBox(width: 8),
                      Text(
                        'Register for Monthly Parking',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
            ),
          ),
          
          SizedBox(height: 16),
          
          // Summary Card
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Monthly Fee:', style: TextStyle(fontWeight: FontWeight.w500)),
                    Text('1000 VND', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue.shade700)),
                  ],
                ),
                SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Setup Fee:', style: TextStyle(fontWeight: FontWeight.w500)),
                    Text('2000 VND', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue.shade700)),
                  ],
                ),
                Divider(),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('Total:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    Text('3000 VND', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.blue.shade700)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildSectionTitle(String title, IconData icon) {
    return Row(
      children: [
        Container(
          padding: EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.blue.shade50,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.blue.shade600, size: 20),
        ),
        SizedBox(width: 12),
        Text(
          title,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
      ],
    );
  }

  Container _searchSection() {
    return Container(
      margin: EdgeInsets.only(top: 40, left: 20, right: 20),
      child: Column(
        children: [
          // Search field
          Container(
            decoration: BoxDecoration(
              boxShadow: [
                BoxShadow(
                  color: Color(0xff1D1617).withValues(alpha: 0.11),
                  spreadRadius: 0,
                  blurRadius: 40,
                ),
              ],
            ),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                filled: true,
                fillColor: Color(0xffF7F8F8),
                hintStyle: TextStyle(
                  color: Color(0xffB6B7B7),
                  fontSize: 14,
                ),
                hintText: 'Search parking by name or address...',
                contentPadding: EdgeInsets.all(20),
                prefixIcon: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Icon(  
                    Icons.search,
                    color: Color(0xffB6B7B7),
                  ),
                ),
                suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      icon: Icon(Icons.clear, color: Color(0xffB6B7B7)),
                      onPressed: () {
                        _searchController.clear();
                      },
                    )
                  : Container(
                      width: 100,
                      child: IntrinsicHeight(
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            VerticalDivider(
                              color: Colors.black,
                              indent: 10,
                              endIndent: 10,
                              thickness: 1,
                            ),
                            Padding(
                              padding: const EdgeInsets.all(8),
                              child: Icon(  
                                Icons.filter_list,
                                color: Color(0xffB6B7B7),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(15),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          
          // Search results dropdown
          if (_showSearchResults && _filteredParkings.isNotEmpty) ...[
            SizedBox(height: 8),
            Container(
              constraints: BoxConstraints(maxHeight: 200),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Color(0xff1D1617).withValues(alpha: 0.1),
                    spreadRadius: 0,
                    blurRadius: 20,
                  ),
                ],
              ),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _filteredParkings.length,
                itemBuilder: (context, index) {
                  final parking = _filteredParkings[index];
                  return ListTile(
                    dense: true,
                    leading: Icon(Icons.local_parking, color: Colors.blue.shade600),
                    title: Text(
                      parking['parking_name'] ?? '',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    subtitle: Text(
                      parking['address'] ?? '',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    onTap: () => _selectParking(parking),
                  );
                },
              ),
            ),
          ],
          
          // No results message
          if (_showSearchResults && _filteredParkings.isEmpty && _searchController.text.isNotEmpty) ...[
            SizedBox(height: 8),
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.search_off, color: Colors.grey.shade500),
                  SizedBox(width: 12),
                  Text(
                    'No parking locations found',
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // Validate form and submit registration
  void _validateAndSubmit() {
    // Check if all required fields are filled
    if (userName.isEmpty) {
      _showErrorMessage('Please wait for user information to load');
      return;
    }
    
    if (_parkingNameController.text.isEmpty || _parkingAddressController.text.isEmpty) {
      _showErrorMessage('Please select a parking lot from the search results');
      return;
    }
    
    if (_selectedParkingId.isEmpty) {
      if (_isLoadingParkingId) {
        _showErrorMessage('Please wait for parking information to load');
      } else {
        _showErrorMessage('Unable to load parking information. Please try selecting the parking lot again');
      }
      return;
    }
    
    if (_licensePlateController.text.isEmpty) {
      _showErrorMessage('Please enter your license plate number');
      return;
    }
    
    if (_vehicleMakeController.text.isEmpty) {
      _showErrorMessage('Please enter your vehicle make and model');
      return;
    }
    
    if (_vehicleColorController.text.isEmpty) {
      _showErrorMessage('Please enter your vehicle color');
      return;
    }
    
    if (_selectedPlan == null) {
      _showErrorMessage('Please select a subscription plan');
      return;
    }
    
    if (!_acceptedTerms) {
      _showErrorMessage('Please accept the terms and conditions');
      return;
    }

    // All validations passed, proceed with registration
    _submitRegistration();
  }

  // Submit the registration form
  void _submitRegistration() async {
    print('=== REGISTRATION SUBMISSION ===');
    print('User ID: $userId');
    print('User Name: $userName');
    print('User Phone: $userPhoneNumber');
    print('Parking ID: $_selectedParkingId');
    print('Parking Name: ${_parkingNameController.text}');
    print('Parking Address: ${_parkingAddressController.text}');
    print('License Plate: ${_licensePlateController.text}');
    print('Vehicle Make: ${_vehicleMakeController.text}');
    print('Vehicle Color: ${_vehicleColorController.text}');
    print('Selected Plan: $_selectedPlan');
    print('Terms Accepted: $_acceptedTerms');
    print('===============================');
    
    // Show loading state
    setState(() {
      _isSubmittingRegistration = true;
    });
    
    try {
      // Call registration API
      final response = await ParkingService.registerMonthlyParking(
        userId: userId,
        parkingId: _selectedParkingId,
        licensePlate: _licensePlateController.text.trim(),
      );
      
      // Handle different response statuses based on API documentation
      final status = response['status'];
      final message = response['message'];
      
      switch (status) {
        case 'success':
          _showSuccessMessage('Đăng ký thành công!');
          _refreshRegisterData(); // Clear form
          // Navigate back to main page after success
          Future.delayed(Duration(seconds: 2), () {
            Navigator.pushNamed(context, '/main');
          });
          break;
          
        case 'exists':
          _showErrorMessage('Biển số xe đã được đăng ký và còn hiệu lực!');
          break;
          
        case 'conflict':
          _showErrorMessage('Biển số xe này đã được người khác đăng ký!');
          break;
          
        case 'not_found':
          _showErrorMessage('Không tìm thấy bãi xe.');
          break;
          
        case 'inactive':
          _showErrorMessage('Bãi xe hiện không hoạt động.');
          break;
          
        case 'fail':
          _showErrorMessage(message ?? 'Lỗi dữ liệu không hợp lệ.');
          break;
          
        default:
          _showErrorMessage('Đã xảy ra lỗi không xác định.');
          print('Unhandled status: $status');
          break;
      }
      
    } catch (e) {
      print('Registration error: $e');
      
      // Handle different types of exceptions
      if (e is NetworkException) {
        _showErrorMessage('Lỗi kết nối đến máy chủ. Vui lòng kiểm tra internet.');
      } else if (e is BadRequestException) {
        _showErrorMessage('Dữ liệu không hợp lệ. Vui lòng kiểm tra thông tin.');
      } else if (e is UnauthorizedException) {
        _showErrorMessage('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      } else {
        _showErrorMessage('Đã xảy ra lỗi. Vui lòng thử lại sau.');
      }
    } finally {
      setState(() {
        _isSubmittingRegistration = false;
      });
    }
  }

  // Refresh/clear registration form data (similar to Unity's refreshRegisterData)
  void _refreshRegisterData() {
    setState(() {
      _searchController.clear();
      _parkingNameController.clear();
      _parkingAddressController.clear();
      _licensePlateController.clear();
      _vehicleMakeController.clear();
      _vehicleColorController.clear();
      _selectedParkingId = '';
      _selectedPlan = null;
      _acceptedTerms = false;
      _showSearchResults = false;
    });
    print('Registration form data cleared');
  }

  // Show error message
  void _showErrorMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: Duration(seconds: 3),
      ),
    );
  }

  // Show success message
  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 3),
      ),
    );
  }

  AppBar _appBar() {
    return AppBar(
      title: const Text(
        'Register',
        style: TextStyle(
          color: Colors.black,
          fontWeight: FontWeight.bold,
          fontSize: 24,
          ),
      ),
      centerTitle: true,
      backgroundColor: Colors.white,
      elevation: 0,
    );
  }
}