import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
// ignore: unused_import
import '../services/payment_service.dart';

class PaymentQRPage extends StatefulWidget {
  final Map<String, dynamic> paymentOrder;

  const PaymentQRPage({super.key, required this.paymentOrder});

  @override
  State<PaymentQRPage> createState() => _PaymentQRPageState();
}

class _PaymentQRPageState extends State<PaymentQRPage> {
  bool _showInstructions = false;

  @override
  Widget build(BuildContext context) {
    final order = widget.paymentOrder;
    final bankInfo = order['bank_info'];

    return Scaffold(
      appBar: AppBar(
        title: Text('Payment'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 1,
        actions: [
          IconButton(
            icon: Icon(Icons.help_outline),
            onPressed: () {
              setState(() {
                _showInstructions = !_showInstructions;
              });
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Order Summary Card
            _buildOrderSummaryCard(),
            SizedBox(height: 24),
            
            // QR Code Section
            _buildQRCodeSection(),
            SizedBox(height: 24),
            
            // Bank Transfer Details
            _buildBankDetailsCard(),
            SizedBox(height: 24),
            
            // Instructions (if shown)
            if (_showInstructions) _buildInstructionsCard(),
            if (_showInstructions) SizedBox(height: 24),
            
            // Action Buttons
            _buildActionButtons(),
            SizedBox(height: 20),
            
            // Important Notes
            _buildImportantNotes(),
          ],
        ),
      ),
    );
  }

  Widget _buildOrderSummaryCard() {
    final order = widget.paymentOrder;
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.receipt_long, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'Order Information',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            _buildInfoRow('Order ID:', order['order_id']),
            _buildInfoRow('Registration Plan:', order['plan_description']),
            _buildInfoRow('License Plate:', order['license_plate']),
            Divider(height: 20),
            _buildInfoRow(
              'Total Amount:', 
              '${order['formatted_amount']} VND',
              isTotal: true,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQRCodeSection() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              'Scan QR code to transfer money',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.blue.shade700,
              ),
            ),
            SizedBox(height: 16),
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: QrImageView(
                data: widget.paymentOrder['qr_data'],
                version: QrVersions.auto,
                size: 200.0,
                backgroundColor: Colors.white,
                foregroundColor: Colors.black,
              ),
            ),
            SizedBox(height: 12),
            Text(
              'Use banking app to scan QR code',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBankDetailsCard() {
    final bankInfo = widget.paymentOrder['bank_info'];
    final order = widget.paymentOrder;
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Bank Transfer Information',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 12),
            _buildCopyableInfoRow('Bank:', bankInfo['bank_name']),
            _buildCopyableInfoRow('Account Number:', bankInfo['account_number']),
            _buildCopyableInfoRow('Account Holder:', bankInfo['account_holder']),
            _buildCopyableInfoRow('Amount:', '${order['formatted_amount']} VND'),
            _buildCopyableInfoRow('Description:', order['transfer_description']),
          ],
        ),
      ),
    );
  }

  Widget _buildCopyableInfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey.shade700,
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => _copyToClipboard(value, label),
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        value,
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                    Icon(
                      Icons.copy,
                      size: 16,
                      color: Colors.blue,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isTotal = false}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey.shade700,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: isTotal ? Colors.blue.shade700 : Colors.black,
              fontSize: isTotal ? 16 : 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructionsCard() {
    return Card(
      elevation: 2,
      color: Colors.blue.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.info_outline, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  'Payment Instructions',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue.shade700,
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            _buildInstructionStep('1', 'Open banking app on your phone'),
            _buildInstructionStep('2', 'Select "Transfer" or "Scan QR" function'),
            _buildInstructionStep('3', 'Scan QR code or enter transfer information'),
            _buildInstructionStep('4', 'Check information and confirm transfer'),
            _buildInstructionStep('5', 'Take screenshot of transaction result for verification'),
          ],
        ),
      ),
    );
  }

  Widget _buildInstructionStep(String step, String instruction) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            decoration: BoxDecoration(
              color: Colors.blue,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                step,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              instruction,
              style: TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          height: 48,
          child: ElevatedButton.icon(
            onPressed: _markAsTransferred,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            icon: Icon(Icons.check, color: Colors.white),
            label: Text(
              'Transfer Completed',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            onPressed: () => Navigator.pop(context),
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: Colors.grey),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            icon: Icon(Icons.arrow_back, color: Colors.grey.shade700),
            label: Text(
              'Go Back',
              style: TextStyle(
                color: Colors.grey.shade700,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildImportantNotes() {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.orange.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: Colors.orange.shade700, size: 20),
              SizedBox(width: 8),
              Text(
                'Important Notes',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.orange.shade700,
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          Text(
            '• Transfer description must be accurate for system verification\n'
            '• Registration will be activated after payment confirmation\n'
            '• Processing time: 1-24 hours during business hours\n'
            '• Contact support if you have payment issues',
            style: TextStyle(
              fontSize: 12,
              color: Colors.orange.shade700,
            ),
          ),
        ],
      ),
    );
  }

  void _copyToClipboard(String text, String type) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Copied $type'),
        duration: Duration(seconds: 2),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _markAsTransferred() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Confirmation'),
        content: Text(
          'Have you completed the transfer?\n\n'
          'Registration will be processed and activated after the system confirms your transaction.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Not Yet'),
          ),
          ElevatedButton(
            onPressed: _confirmTransfer,
            child: Text('Transferred'),
          ),
        ],
      ),
    );
  }

  void _confirmTransfer() {
    Navigator.pop(context); // Close dialog
    Navigator.pop(context, 'payment_initiated'); // Return to registration with result
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Thank you! Registration will be activated after payment confirmation.',
        ),
        duration: Duration(seconds: 3),
        backgroundColor: Colors.green,
      ),
    );
  }
}