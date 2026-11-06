import csv
import io
import json
from pathlib import Path
import subprocess
import unittest


class WorkspaceCsvTextTests(unittest.TestCase):
    def test_downloads_escape_formula_like_text_and_preserve_normal_cells(self):
        html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")

        def section(start, end):
            offset = html.index(start)
            return html[offset:html.index(end, offset)]

        script = r"""
const downloads = [];
let current;
const URL = {
  createObjectURL(blob) { current = blob; return 'blob:fixture'; },
  revokeObjectURL() {}
};
const document = {
  createElement() { return { click() { downloads.push(current.text()); }, remove() {} }; },
  getElementById() { return null; },
  body: { appendChild() {} }
};
const root = { hofPlatform: { brokerageAgents: [{
  name: '  ＋1', email: 'agent@example.test', teamName: '\tOperations',
  usage: { used: 12 }, nextAction: '@SUM(1,2)'
}] } };
const window = { setTimeout() {} };
const state = { offers: [
  { property_address: '=1+2";,=3+4', buyer_name: 'Élodie, "Lee"', offer_price: 425000 },
  { property_address: '19 Cedar Court', buyer_name: '\n-1', offer_price: 510000 }
] };
const sortedOffers = offers => offers;
const offerBuyerName = offer => offer.buyer_name;
const cleanStatus = () => 'Draft';
const signingLabel = () => 'Not sent';
const brokerageAgentBillingWindow = () => '';
const brokerageAgentDate = () => '';
"""
        script += section('<script id="hof-spreadsheet-csv">', "</script>").split(">", 1)[1]
        script += section("  root.hofExportVisibleOffers =", "  root.hofSetOfferWorkspaceFilter =")
        script += section("  root.exportBrokerageRoster =", "  root.renderBrokerageBrandPreview =")
        script += """
root.hofExportVisibleOffers();
root.exportBrokerageRoster();
Promise.all(downloads).then(files => process.stdout.write(JSON.stringify(files)));
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        offers, roster = [list(csv.reader(io.StringIO(file))) for file in json.loads(result.stdout)]
        self.assertEqual(offers[1][:3], ["'=1+2\";,=3+4", 'Élodie, "Lee"', "425000"])
        self.assertEqual(offers[2][:3], ["19 Cedar Court", "'\n-1", "510000"])
        self.assertEqual(len(offers[1]), len(offers[0]))
        self.assertEqual(roster[1][:4], ["'  ＋1", "agent@example.test", "pending", "'\tOperations"])
        self.assertEqual(roster[1][7], "12")
        self.assertEqual(roster[1][13], "'@SUM(1,2)")
