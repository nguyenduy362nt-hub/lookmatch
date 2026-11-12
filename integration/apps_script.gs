// Dán vào Google Sheet: Tiện ích mở rộng > Apps Script. Triển khai > Ứng dụng web:
//   Thực thi với tư cách: Tôi · Ai có quyền truy cập: Bất kỳ ai.
// Cài khoá bí mật: Cài đặt dự án > Thuộc tính tập lệnh > thêm KEY = <chuỗi ngẫu nhiên dài>.
function doPost(e) {
  var d = JSON.parse(e.postData.contents);
  var key = PropertiesService.getScriptProperties().getProperty('KEY');
  if (!key || d.key !== key) {
    return ContentService.createTextOutput(JSON.stringify({ok: false, error: 'sai khoa'}))
      .setMimeType(ContentService.MimeType.JSON);
  }
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('nhat_ky') || ss.insertSheet('nhat_ky');
  if (sh.getLastRow() === 0) {
    sh.appendRow(['thoi_gian', 'ten_file', 'top1', 'diem_top1', 'ms', 'nguon_danh_muc']);
  }
  sh.appendRow([d.time, d.file, d.top1, d.score, d.ms, d.catalog]);
  return ContentService.createTextOutput(JSON.stringify({ok: true}))
    .setMimeType(ContentService.MimeType.JSON);
}
