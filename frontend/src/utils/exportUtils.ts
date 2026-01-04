import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';
import { Identity, SearchResult, ExportOptions } from '../types';

export const exportToCSV = (data: any[], filename: string): void => {
  const headers = Object.keys(data[0] || {});
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(h => JSON.stringify(row[h] || '')).join(',')),
  ].join('\n');

  downloadFile(csvContent, filename, 'text/csv');
};

export const exportToJSON = (data: any, filename: string): void => {
  const jsonContent = JSON.stringify(data, null, 2);
  downloadFile(jsonContent, filename, 'application/json');
};

export const exportToExcel = (data: any[], filename: string, sheetName = 'Sheet1'): void => {
  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  XLSX.writeFile(workbook, filename);
};

export const exportToPDF = (identity: Identity, options: ExportOptions): void => {
  const doc = new jsPDF();
  let yPosition = 20;

  doc.setFontSize(18);
  doc.text('OSINT Intelligence Report', 20, yPosition);
  yPosition += 10;

  doc.setFontSize(12);
  doc.text(`Subject: ${identity.name}`, 20, yPosition);
  yPosition += 7;
  doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, yPosition);
  yPosition += 10;

  if (identity.email) {
    doc.text(`Email: ${identity.email}`, 20, yPosition);
    yPosition += 7;
  }

  if (identity.phone) {
    doc.text(`Phone: ${identity.phone}`, 20, yPosition);
    yPosition += 7;
  }

  yPosition += 5;

  if (identity.profiles && identity.profiles.length > 0) {
    doc.setFontSize(14);
    doc.text('Social Media Profiles', 20, yPosition);
    yPosition += 7;

    const profileData = identity.profiles.map(p => [
      p.platform,
      p.username,
      p.url,
    ]);

    autoTable(doc, {
      startY: yPosition,
      head: [['Platform', 'Username', 'URL']],
      body: profileData,
    });

    yPosition = (doc as any).lastAutoTable.finalY + 10;
  }

  if (identity.employment && identity.employment.length > 0) {
    doc.setFontSize(14);
    doc.text('Employment History', 20, yPosition);
    yPosition += 7;

    const employmentData = identity.employment.map(e => [
      e.company,
      e.title,
      e.current ? 'Current' : e.endDate || 'N/A',
    ]);

    autoTable(doc, {
      startY: yPosition,
      head: [['Company', 'Title', 'Status']],
      body: employmentData,
    });
  }

  doc.save(`osint-report-${identity.id}.pdf`);
};

export const exportToHTML = (identity: Identity): void => {
  const html = `
<!DOCTYPE html>
<html>
<head>
  <title>OSINT Report - ${identity.name}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
    h1 { color: #333; }
    .section { margin: 20px 0; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f4f4f4; }
  </style>
</head>
<body>
  <h1>OSINT Intelligence Report</h1>
  <div class="section">
    <h2>Subject Information</h2>
    <p><strong>Name:</strong> ${identity.name}</p>
    ${identity.email ? `<p><strong>Email:</strong> ${identity.email}</p>` : ''}
    ${identity.phone ? `<p><strong>Phone:</strong> ${identity.phone}</p>` : ''}
    <p><strong>Confidence Score:</strong> ${Math.round(identity.confidenceScore * 100)}%</p>
  </div>
  
  ${identity.profiles && identity.profiles.length > 0 ? `
  <div class="section">
    <h2>Social Media Profiles</h2>
    <table>
      <tr><th>Platform</th><th>Username</th><th>URL</th></tr>
      ${identity.profiles.map(p => `
        <tr>
          <td>${p.platform}</td>
          <td>${p.username}</td>
          <td><a href="${p.url}" target="_blank">${p.url}</a></td>
        </tr>
      `).join('')}
    </table>
  </div>
  ` : ''}
  
  ${identity.employment && identity.employment.length > 0 ? `
  <div class="section">
    <h2>Employment History</h2>
    <table>
      <tr><th>Company</th><th>Title</th><th>Duration</th></tr>
      ${identity.employment.map(e => `
        <tr>
          <td>${e.company}</td>
          <td>${e.title}</td>
          <td>${e.startDate || 'N/A'} - ${e.current ? 'Present' : (e.endDate || 'N/A')}</td>
        </tr>
      `).join('')}
    </table>
  </div>
  ` : ''}
</body>
</html>
  `;

  downloadFile(html, `osint-report-${identity.id}.html`, 'text/html');
};

const downloadFile = (content: string, filename: string, mimeType: string): void => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
