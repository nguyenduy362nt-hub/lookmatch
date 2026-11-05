import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const apiBase = 'http://localhost:8000';
void main() => runApp(const MaterialApp(home: SearchPage()));

class SearchPage extends StatefulWidget {
  const SearchPage({super.key});
  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  List<dynamic> results = [];
  String? error;
  bool loading = false;

  Future<void> pickAndSearch() async {
    final x = await ImagePicker().pickImage(source: ImageSource.gallery);
    if (x == null) return;
    setState(() { loading = true; error = null; results = []; });
    try {
      final req = http.MultipartRequest('POST', Uri.parse('$apiBase/search'))
        ..files.add(http.MultipartFile.fromBytes('file', await x.readAsBytes(), filename: x.name));
      final res = await http.Response.fromStream(await req.send());
      if (res.statusCode == 200) {
        results = jsonDecode(res.body)['results'];
      } else {
        error = jsonDecode(utf8.decode(res.bodyBytes))['detail'].toString();
      }
    } catch (e) {
      error = 'Không kết nối được server: $e';
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('LookMatch')),
    floatingActionButton: FloatingActionButton.extended(
        onPressed: pickAndSearch, icon: const Icon(Icons.image_search), label: const Text('Chọn ảnh khách')),
    body: loading
        ? const Center(child: CircularProgressIndicator())
        : error != null
        ? Center(child: Text(error!))
        : ListView(children: [
      for (final r in results)
        ListTile(
            leading: CircleAvatar(child: Text('${r['rank']}')),
            title: Text(r['product_id']),
            subtitle: Text('độ giống: ${r['score']}')),
    ]),
  );
}
