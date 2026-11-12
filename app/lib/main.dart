import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

// Windows/Chrome -> http://localhost:8000 ; máy ảo Android -> http://10.0.2.2:8000
const apiBase = 'http://localhost:8000';
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
  String? error;
  bool loading = false;

  Future<void> pickAndSearch() async {
    final x = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (x == null) return;
    setState(() { loading = true; error = null; results = []; replyText = ''; });
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$apiBase/search'))
        ..files.add(http.MultipartFile.fromBytes('file', await x.readAsBytes(), filename: x.name));
      final res = await http.Response.fromStream(await req.send());
      final body = jsonDecode(utf8.decode(res.bodyBytes));
      if (res.statusCode == 200) {
        results = body['results'];
        replyText = (body['reply_text'] ?? '').toString();
        catalogSource = (body['catalog'] ?? '').toString();
      } else {
        error = body['detail'].toString();
      }
    } catch (e) {
      error = 'Không kết nối được server: $e';
    }
    setState(() => loading = false);
  }

  Future<void> refreshCatalog() async {
    try {
      final res = await http.post(Uri.parse('$apiBase/catalog/refresh'));
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
