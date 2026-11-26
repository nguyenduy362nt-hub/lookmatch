import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

// Windows/Chrome -> http://localhost:8000 ; máy ảo Android -> http://10.0.2.2:8000
const apiBase = 'http://localhost:8000';
// Khoá API đưa vào lúc chạy: flutter run -d chrome --dart-define=LOOKMATCH_API_KEY=<khoá>. KHÔNG ghi cứng khoá trong code.
// Lưu ý: app web gửi khoá trong trình duyệt nên khoá chỉ chống truy cập ngẫu nhiên, không thay cho đăng nhập từng người.
const apiKey = String.fromEnvironment('LOOKMATCH_API_KEY');
Map<String, String> authHeaders([Map<String, String>? extra]) =>
    {if (apiKey.isNotEmpty) 'X-API-Key': apiKey, ...?extra};

String friendlyError(int status, dynamic detail) {
  switch (status) {
    case 401:
      return 'Chưa được phép dùng: thiếu hoặc sai khoá API (hỏi người quản trị).';
    case 413:
      return 'Ảnh quá lớn, hãy chọn ảnh nhỏ hơn 8 MB.';
    case 415:
      return 'Chỉ nhận ảnh JPEG, PNG hoặc WebP.';
    case 429:
      return 'Bạn thao tác quá nhanh, chờ ít giây rồi thử lại.';
    default:
      return detail.toString();
  }
}
// ---- Giao diện (W07: sửa theo góp ý người dùng: đơn điệu, cần rõ cách dùng, cần thực tế hơn) ----
// Bảng màu kiểu công nghệ: nền xanh đen, nhấn chàm - xanh lơ
const kBg = Color(0xFF0B1020);
const kCard = Color(0xFF141B34);
const kBorder = Color(0xFF26304F);
const kMuted = Color(0xFF9AA4C7);
const kAccent = Color(0xFF6366F1);
const kAccent2 = Color(0xFF22D3EE);
const kGlow = Color(0x596366F1);
const kGrad = LinearGradient(colors: [Color(0xFF6366F1), Color(0xFF22D3EE)]);

String nameOf(dynamic r) {
  final t = (r['ten'] ?? '').toString();
  return t.isNotEmpty ? t : (r['product_id'] ?? '').toString();
}

double scoreOf(dynamic r) {
  final s = double.tryParse((r['score'] ?? '0').toString()) ?? 0.0;
  return s.clamp(0.0, 1.0).toDouble();
}

String percentOf(dynamic r) => '${(scoreOf(r) * 100).round()}%';
String priceOf(dynamic r) => (r['gia'] ?? '').toString();

void main() => runApp(const LookMatchApp());

class LookMatchApp extends StatelessWidget {
  const LookMatchApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'LookMatch',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          colorSchemeSeed: kAccent,
          scaffoldBackgroundColor: kBg,
        ),
        home: const SearchPage(),
      );
}

// Chữ có màu chuyển sắc
class GradientText extends StatelessWidget {
  final String text;
  final TextStyle style;
  const GradientText(this.text, {super.key, required this.style});
  @override
  Widget build(BuildContext context) => ShaderMask(
        shaderCallback: (b) => kGrad.createShader(Rect.fromLTWH(0, 0, b.width, b.height)),
        child: Text(text, textAlign: TextAlign.center, style: style.copyWith(color: Colors.white)),
      );
}

// Nút chính: nền chuyển sắc, có ánh sáng
class GradientButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onPressed;
  const GradientButton({super.key, required this.label, required this.icon, required this.onPressed});
  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(
          gradient: kGrad,
          borderRadius: BorderRadius.circular(14),
          boxShadow: const [BoxShadow(color: kGlow, blurRadius: 24, offset: Offset(0, 8))],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: onPressed,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(icon, color: Colors.white),
                const SizedBox(width: 10),
                Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16)),
              ]),
            ),
          ),
        ),
      );
}

// Khung thẻ tối có viền mảnh
Widget panel({required Widget child, EdgeInsets padding = const EdgeInsets.all(16)}) => Container(
      padding: padding,
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: kBorder),
      ),
      child: child,
    );

class SearchPage extends StatefulWidget {
  const SearchPage({super.key});
  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  List<dynamic> results = [];
  String replyText = '';
  String catalogSource = '';
  String searchId = '';
  String feedbackMsg = '';
  String? error;
  bool loading = false;
  Uint8List? queryBytes;

  Future<void> pickAndSearch() async {
    final x = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (x == null) return;
    final bytes = await x.readAsBytes();
    setState(() {
      loading = true;
      error = null;
      results = [];
      replyText = '';
      searchId = '';
      feedbackMsg = '';
      queryBytes = bytes;
    });
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$apiBase/search'))
        ..headers.addAll(authHeaders())
        ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: x.name));
      final res = await http.Response.fromStream(await req.send());
      final body = jsonDecode(utf8.decode(res.bodyBytes));
      if (res.statusCode == 200) {
        results = body['results'];
        replyText = (body['reply_text'] ?? '').toString();
        searchId = (body['search_id'] ?? '').toString();
        catalogSource = (body['catalog'] ?? '').toString();
      } else {
        error = friendlyError(res.statusCode, body['detail']);
      }
    } catch (e) {
      error = 'Không kết nối được server: $e';
    }
    setState(() => loading = false);
  }

  // Tính năng #3: báo kết quả đúng/sai; mã đúng chọn từ danh sách top-10 (hoặc nhập tay)
  Future<void> sendFeedback(String verdict, {String? trueProduct}) async {
    try {
      final res = await http.post(Uri.parse('$apiBase/feedback'),
          headers: authHeaders({'Content-Type': 'application/json'}),
          body: jsonEncode({'search_id': searchId, 'verdict': verdict, 'true_product': trueProduct}));
      final b = jsonDecode(utf8.decode(res.bodyBytes));
      setState(() => feedbackMsg = res.statusCode == 200
          ? 'Đã ghi phản hồi, cảm ơn!'
          : 'Không ghi được: ${friendlyError(res.statusCode, b['detail'])}');
    } catch (e) {
      setState(() => feedbackMsg = 'Lỗi gửi phản hồi: $e');
    }
  }

  Future<void> askWrong() async {
    String? picked;
    final ctl = TextEditingController();
    picked = await showDialog<String>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Mẫu đúng là mẫu nào?'),
        content: SizedBox(
          width: 360,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            for (final r in results.skip(1).take(4))
              ListTile(
                  dense: true,
                  title: Text(nameOf(r)),
                  subtitle: Text('hạng ${r['rank']} · ${r['product_id']}'),
                  onTap: () => Navigator.pop(c, r['product_id'])),
            TextField(controller: ctl, decoration: const InputDecoration(labelText: 'Hoặc nhập mã mẫu đúng')),
          ]),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c), child: const Text('Huỷ')),
          TextButton(onPressed: () => Navigator.pop(c, ctl.text.trim()), child: const Text('Gửi')),
        ],
      ),
    );
    if (picked != null && picked.isNotEmpty) sendFeedback('sai', trueProduct: picked);
  }

  Future<void> refreshCatalog() async {
    try {
      final res = await http.post(Uri.parse('$apiBase/catalog/refresh'), headers: authHeaders());
      final b = jsonDecode(utf8.decode(res.bodyBytes));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Đã làm mới danh mục: ${b['so_mau']} mẫu (nguồn: ${b['nguon']})')));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lỗi làm mới: $e')));
    }
  }

  void copyReply() {
    Clipboard.setData(ClipboardData(text: replyText));
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Đã sao chép, dán vào Zalo cho khách')));
  }

  // Thanh độ giống chuyển sắc, kèm phần trăm
  Widget scoreBar(dynamic r) => Row(children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Stack(children: [
              Container(height: 8, color: kBorder),
              FractionallySizedBox(
                widthFactor: scoreOf(r),
                child: Container(height: 8, decoration: const BoxDecoration(gradient: kGrad)),
              ),
            ]),
          ),
        ),
        const SizedBox(width: 10),
        Text(percentOf(r), style: const TextStyle(fontWeight: FontWeight.bold, color: kAccent2)),
      ]);

  Widget tag(String text) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: kBorder),
          color: const Color(0xFF111833),
        ),
        child: Text(text, style: const TextStyle(fontSize: 12, color: kMuted)),
      );

  Widget step(int n, String text) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: panel(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Container(
              width: 32,
              height: 32,
              alignment: Alignment.center,
              decoration: const BoxDecoration(gradient: kGrad, shape: BoxShape.circle),
              child: Text('$n', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(width: 14),
            Expanded(child: Text(text, style: const TextStyle(fontSize: 15))),
          ]),
        ),
      );

  // Màn hình đầu: giới thiệu và hướng dẫn 3 bước
  Widget emptyState() => Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 96),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  gradient: kGrad,
                  borderRadius: BorderRadius.circular(28),
                  boxShadow: const [BoxShadow(color: kGlow, blurRadius: 40, offset: Offset(0, 12))],
                ),
                child: const Icon(Icons.image_search, size: 52, color: Colors.white),
              ),
              const SizedBox(height: 24),
              const GradientText('Tìm mẫu giống ảnh khách gửi',
                  style: TextStyle(fontSize: 34, fontWeight: FontWeight.w800, height: 1.15)),
              const SizedBox(height: 10),
              const Text('Chọn ảnh khách, app gợi ý các mẫu trong shop giống nhất.',
                  textAlign: TextAlign.center, style: TextStyle(color: kMuted, fontSize: 16)),
              const SizedBox(height: 16),
              Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: [
                tag('Tìm theo hình ảnh'),
                tag('CLIP ViT-B/32'),
                tag('Shop Quý Hòa'),
              ]),
              const SizedBox(height: 28),
              step(1, 'Bấm "Chọn ảnh khách" và chọn ảnh khách gửi qua Zalo.'),
              step(2, 'Xem mẫu giống nhất và độ giống (%) ở đầu danh sách.'),
              step(3, 'Bấm "Sao chép" để dán tin trả lời khách, rồi bấm Đúng hoặc Sai để báo kết quả.'),
              const SizedBox(height: 20),
              GradientButton(label: 'Chọn ảnh khách', icon: Icons.image_search, onPressed: pickAndSearch),
            ]),
          ),
        ),
      );

  Widget loadingState() => const Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          CircularProgressIndicator(color: kAccent2),
          SizedBox(height: 16),
          Text('Đang tìm mẫu giống...', style: TextStyle(color: kMuted)),
        ]),
      );

  Widget errorState() => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error_outline, size: 56, color: Color(0xFFF87171)),
            const SizedBox(height: 12),
            Text(error!, textAlign: TextAlign.center),
            const SizedBox(height: 20),
            GradientButton(label: 'Chọn ảnh khác', icon: Icons.image_search, onPressed: pickAndSearch),
          ]),
        ),
      );

  // Mẫu giống nhất: thẻ lớn viền chuyển sắc, có giá và nút sao chép tin trả khách
  Widget topCard(dynamic r) {
    final price = priceOf(r);
    return Container(
      padding: const EdgeInsets.all(1.5),
      decoration: BoxDecoration(
        gradient: kGrad,
        borderRadius: BorderRadius.circular(22),
        boxShadow: const [BoxShadow(color: kGlow, blurRadius: 30, offset: Offset(0, 10))],
      ),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: kCard, borderRadius: BorderRadius.circular(20.5)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(gradient: kGrad, borderRadius: BorderRadius.circular(20)),
            child: const Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(Icons.star, size: 16, color: Colors.white),
              SizedBox(width: 6),
              Text('Giống nhất', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
            ]),
          ),
          const SizedBox(height: 12),
          Text(nameOf(r), style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
          if (price.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(price, style: const TextStyle(fontSize: 18, color: kAccent2, fontWeight: FontWeight.w600)),
            ),
          const SizedBox(height: 14),
          scoreBar(r),
          if (replyText.isNotEmpty) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF0F1630),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: kBorder),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Expanded(child: Text(replyText, style: const TextStyle(height: 1.4))),
                const SizedBox(width: 10),
                FilledButton.tonalIcon(
                    onPressed: copyReply, icon: const Icon(Icons.copy, size: 18), label: const Text('Sao chép')),
              ]),
            ),
          ],
        ]),
      ),
    );
  }

  Widget feedbackCard() => panel(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Mẫu giống nhất có đúng không?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 4),
          const Text('Phản hồi của bạn được ghi lại để cải thiện app.', style: TextStyle(fontSize: 13, color: kMuted)),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
            FilledButton.icon(
                style: FilledButton.styleFrom(backgroundColor: const Color(0xFF16A34A), foregroundColor: Colors.white),
                onPressed: () => sendFeedback('dung'),
                icon: const Icon(Icons.check),
                label: const Text('Đúng')),
            OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFF87171), side: const BorderSide(color: Color(0xFFF87171))),
                onPressed: askWrong,
                icon: const Icon(Icons.close),
                label: const Text('Sai')),
            TextButton(onPressed: () => sendFeedback('khong_co'), child: const Text('Shop không có mẫu này')),
          ]),
          if (feedbackMsg.isNotEmpty)
            Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Text(feedbackMsg, style: const TextStyle(color: kAccent2))),
        ]),
      );

  Widget otherCard(dynamic r) {
    final price = priceOf(r);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: panel(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          Container(
            width: 38,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF1E2747),
              border: Border.all(color: kBorder),
            ),
            child: Text('${r['rank']}', style: const TextStyle(color: kAccent2, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(nameOf(r), style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
              if (price.isNotEmpty) Text(price, style: const TextStyle(color: kMuted)),
              const SizedBox(height: 8),
              scoreBar(r),
            ]),
          ),
        ]),
      ),
    );
  }

  Widget resultList() => Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 96), children: [
            if (queryBytes != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Row(children: [
                  Container(
                    padding: const EdgeInsets.all(2),
                    decoration: BoxDecoration(gradient: kGrad, borderRadius: BorderRadius.circular(16)),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(14),
                      child: Image.memory(queryBytes!, width: 88, height: 88, fit: BoxFit.cover),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Ảnh khách vừa chọn', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text('Tìm thấy ${results.length} mẫu giống nhất', style: const TextStyle(color: kMuted)),
                      if (catalogSource.isNotEmpty)
                        Text('Danh mục lấy từ: $catalogSource', style: const TextStyle(fontSize: 12, color: kMuted)),
                    ]),
                  ),
                ]),
              ),
            topCard(results.first),
            const SizedBox(height: 12),
            if (searchId.isNotEmpty) feedbackCard(),
            if (results.length > 1)
              const Padding(
                padding: EdgeInsets.only(top: 20, bottom: 10),
                child: Text('Các mẫu khác', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            for (final r in results.skip(1)) otherCard(r),
          ]),
        ),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: kBg,
        appBar: AppBar(
          backgroundColor: kBg,
          surfaceTintColor: Colors.transparent,
          title: Row(mainAxisSize: MainAxisSize.min, children: [
            ShaderMask(
              shaderCallback: (b) => kGrad.createShader(Rect.fromLTWH(0, 0, b.width, b.height)),
              child: const Icon(Icons.image_search, color: Colors.white),
            ),
            const SizedBox(width: 10),
            const Text('LookMatch', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.5)),
          ]),
          actions: [
            IconButton(
                tooltip: 'Làm mới danh mục từ Google Sheets',
                onPressed: refreshCatalog,
                icon: const Icon(Icons.sync)),
          ],
        ),
        floatingActionButton: FloatingActionButton.extended(
            backgroundColor: kAccent,
            foregroundColor: Colors.white,
            onPressed: pickAndSearch,
            icon: const Icon(Icons.image_search),
            label: const Text('Chọn ảnh khách')),
        body: Container(
          decoration: const BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0, -1.1),
              radius: 1.3,
              colors: [Color(0xFF1B2250), kBg],
            ),
          ),
          child: loading
              ? loadingState()
              : error != null
                  ? errorState()
                  : results.isEmpty
                      ? emptyState()
                      : resultList(),
        ),
      );
}
