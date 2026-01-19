// import 'dart:convert'; when use for JSON encoding if needed
class PaymentService {
  // Bank account info for receiving payments
  static const String BANK_NAME = "MB Bank";
  static const String ACCOUNT_NUMBER = "1234567890";
  static const String ACCOUNT_HOLDER = "NGUYEN VAN A";
  static const String BANK_CODE = "MB";

  // Generate QR code data for bank transfer
  static String generateBankTransferQR({
    required String orderId,
    required int amount,
    required String description,
  }) {
    // // VietQR format 
    // final qrData = {
    //   "bank": BANK_CODE,
    //   "account": ACCOUNT_NUMBER,
    //   "amount": amount.toString(),
    //   "description": description,
    //   "template": "compact"
    // };
    
    
    final transferInfo = "Bank: $BANK_NAME\n"
        "Account: $ACCOUNT_NUMBER\n"
        "Account Holder: $ACCOUNT_HOLDER\n"
        "Amount: ${formatCurrency(amount)} VND\n"
        "Description: $description";
    
    return transferInfo;
  }

  // Generate VietQR standard format (if banks support it)
  static String generateVietQR({
    required String orderId,
    required int amount,
    required String description,
  }) {
    // Simplified VietQR format
    return "2|01|$BANK_CODE|$ACCOUNT_NUMBER|$ACCOUNT_HOLDER|$amount|$description|VN";
  }

  // Format currency for display
  static String formatCurrency(int amount) {
    return amount.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
  }

  // Generate payment order details
  static Map<String, dynamic> generatePaymentOrder({
    required String userId,
    required String parkingId,
    required String licensePlate,
    required String planType,
  }) {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final orderId = "SP${timestamp.toString().substring(7)}"; // SP + last 6 digits
    
    // Calculate amount based on plan
    int amount;
    String planDescription;
    
    switch (planType) {
      case '1month':
        amount = 1000; // 1,000,000 VND
        planDescription = "1 Month Plan";
        break;
      case '3months':
        amount = 2800; // 2,800,000 VND (save 200k)
        planDescription = "3 Month Plan";
        break;
      case '6months':
        amount = 5500; // 5,500,000 VND (save 500k)
        planDescription = "6 Month Plan";
        break;
      case '12months':
        amount = 10000; // 10,000,000 VND (save 2M)
        planDescription = "12 Month Plan";
        break;
      default:
        amount = 1000;
        planDescription = "1 Month Plan";
    }

    final description = "SmartParking $planDescription $licensePlate $orderId";

    return {
      'order_id': orderId,
      'user_id': userId,
      'parking_id': parkingId,
      'license_plate': licensePlate,
      'plan_type': planType,
      'plan_description': planDescription,
      'amount': amount,
      'formatted_amount': formatCurrency(amount),
      'transfer_description': description,
      'qr_data': generateBankTransferQR(
        orderId: orderId,
        amount: amount,
        description: description,
      ),
      'viet_qr': generateVietQR(
        orderId: orderId,
        amount: amount,
        description: description,
      ),
      'bank_info': {
        'bank_name': BANK_NAME,
        'account_number': ACCOUNT_NUMBER,
        'account_holder': ACCOUNT_HOLDER,
        'bank_code': BANK_CODE,
      },
      'created_at': DateTime.now().toIso8601String(),
      'status': 'pending_payment',
    };
  }

  // Create pending registration (to be confirmed after payment)
  static Map<String, dynamic> createPendingRegistration({
    required Map<String, dynamic> paymentOrder,
  }) {
    return {
      'order_id': paymentOrder['order_id'],
      'user_id': paymentOrder['user_id'],
      'parking_id': paymentOrder['parking_id'],
      'license_plate': paymentOrder['license_plate'],
      'plan_type': paymentOrder['plan_type'],
      'amount_expected': paymentOrder['amount'],
      'transfer_description': paymentOrder['transfer_description'],
      'status': 'pending_payment',
      'created_at': paymentOrder['created_at'],
      'expires_at': DateTime.now().add(Duration(hours: 24)).toIso8601String(), // 24h to complete payment
    };
  }

  // Instructions for manual verification (for admin)
  static String getPaymentVerificationInstructions() {
    return """
PAYMENT VERIFICATION INSTRUCTIONS:

1. Check bank transaction history
2. Find transaction with exact description
3. Confirm correct amount
4. Update registration status to 'active'
5. Send confirmation notification to user

Note: Transfer description must be accurate for automatic reconciliation.
    """;
  }
}