import 'dart:convert';
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
void main() => runApp(const MaterialApp(home: SearchPage()));

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

  Future<void> pickAndSearch() async {
    final x = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (x == null) return;
    setState(() { loading = true; error = null; results = []; replyText = ''; searchId = ''; feedbackMsg = ''; });
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$apiBase/search'))
        ..headers.addAll(authHeaders())
        ..files.add(http.MultipartFile.fromBytes('file', await x.readAsBytes(), filename: x.name));
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
                  title: Text((r['ten'] ?? '').toString().isNotEmpty ? r['ten'] : r['product_id']),
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

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('LookMatch'), actions: [
          IconButton(
              tooltip: 'Làm mới danh mục từ Google Sheets',
              onPressed: refreshCatalog,
              icon: const Icon(Icons.sync)),
        ]),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: pickAndSearch, icon: const Icon(Icons.image_search), label: const Text('Chọn ảnh khách')),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : error != null
                ? Center(child: Text(error!))
                : ListView(children: [
                    if (replyText.isNotEmpty)
                      Card(
                        margin: const EdgeInsets.all(12),
                        child: ListTile(
                          title: Text(replyText),
                          subtitle: Text('Danh mục lấy từ: $catalogSource'),
                          trailing: IconButton(
                            tooltip: 'Sao chép tin nhắn trả khách',
                            icon: const Icon(Icons.copy),
                            onPressed: () {
                              Clipboard.setData(ClipboardData(text: replyText));
                              ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Đã sao chép, dán vào Zalo cho khách')));
                            },
                          ),
                        ),
                      ),
                    if (searchId.isNotEmpty && results.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                          const Text('Mẫu hạng 1 có đúng không?'),
                          FilledButton.tonal(onPressed: () => sendFeedback('dung'), child: const Text('Đúng')),
                          FilledButton.tonal(onPressed: askWrong, child: const Text('Sai')),
                          TextButton(onPressed: () => sendFeedback('khong_co'), child: const Text('Shop không có mẫu này')),
                          if (feedbackMsg.isNotEmpty) Text(feedbackMsg),
                        ]),
                      ),
                    for (final r in results)
                      ListTile(
                        leading: CircleAvatar(child: Text('${r['rank']}')),
                        title: Text((r['ten'] ?? '').toString().isNotEmpty ? r['ten'] : r['product_id']),
                        subtitle: Text(
                            '${r['product_id']} · độ giống: ${r['score']}${(r['gia'] ?? '').toString().isNotEmpty ? ' · ${r['gia']}' : ''}'),
                      ),
                  ]),
      );
}
