"""Generate BattGPT UML class model (.drawio) in the ERAS reference notation."""
from xml.sax.saxutils import escape as _esc
def escape(s):
    return _esc(str(s), {'"': "&quot;", "'": "&apos;"})

GREY  = "#D9D9D9"   # imported / upper ontology (EMMO, BattINFO)  — ERAS TLO grey
WHITE = "#FFFFFF"   # BattGPT core structural classes             — ERAS NEP white
CYAN  = "#AEE6EC"   # BattGPT classification vocabulary           — ERAS NORN cyan
PINK  = "#F8CECC"   # M0 instances                                — ERAS instance pink

ROW = 16      # attribute row height
HDR = 26      # class-name compartment height

class Page:
    def __init__(self, name):
        self.name, self.cells, self.n = name, [], 0
    def _id(self, p="n"):
        self.n += 1
        return f"{p}{self.n}"

    def cls(self, x, y, w, name, attrs=(), fill=WHITE, stereo=None):
        """UML class: name compartment + attribute compartment."""
        cid = self._id("c")
        hdr = HDR + (14 if stereo else 0)
        h = hdr + ROW * len(attrs)
        label = escape((f"\u00ab{stereo}\u00bb<br/>" if stereo else "") + name)
        st = (f"swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;"
              f"horizontal=1;startSize={hdr};horizontalStack=0;resizeParent=0;resizeParentMax=0;"
              f"html=1;collapsible=0;marginBottom=0;whiteSpace=wrap;fontSize=11;"
              f"fillColor={fill};strokeColor=#000000;")
        self.cells.append(f'<mxCell id="{cid}" value="{label}" style="{st}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        for i, a in enumerate(attrs):
            ast = ("text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=6;"
                   "spacingRight=6;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];"
                   "portConstraint=eastwest;whiteSpace=wrap;html=1;fontSize=10;")
            self.cells.append(f'<mxCell id="{cid}_a{i}" value="{escape(a)}" style="{ast}" vertex="1" parent="{cid}">'
                              f'<mxGeometry y="{hdr + i*ROW}" width="{w}" height="{ROW}" as="geometry"/></mxCell>')
        return cid

    def box(self, x, y, w, name, fill=WHITE, h=30, bold=True, italic=False, underline=False, fs=11):
        cid = self._id("b")
        style = 1 if bold else 0
        if italic: style += 2
        if underline: style += 4
        st = (f"rounded=0;whiteSpace=wrap;html=1;fontSize={fs};fontStyle={style};"
              f"fillColor={fill};strokeColor=#000000;verticalAlign=middle;")
        self.cells.append(f'<mxCell id="{cid}" value="{escape(name)}" style="{st}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def note(self, x, y, w, h, text, fs=10, align="left"):
        cid = self._id("t")
        st = (f"text;html=1;whiteSpace=wrap;fontSize={fs};align={align};verticalAlign=top;"
              f"strokeColor=none;fillColor=none;")
        self.cells.append(f'<mxCell id="{cid}" value="{escape(text)}" style="{st}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def legend(self, x, y, w, h, text):
        cid = self._id("lg")
        st = ("rounded=0;whiteSpace=wrap;html=1;fontSize=10;align=left;verticalAlign=top;"
              "fillColor=#FBFBFB;strokeColor=#999999;dashed=1;spacingLeft=6;spacingTop=2;")
        self.cells.append(f'<mxCell id="{cid}" value="{escape(text)}" style="{st}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def edge(self, src, tgt, label="", kind="assoc", exit=None, entry=None, pts=None, lx=None, ly=None):
        eid = self._id("e")
        base = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;fontSize=10;labelBackgroundColor=#FFFFFF;"
        kinds = {
            "gen":     "endArrow=block;endFill=0;endSize=12;",                                   # generalization
            "assoc":   "endArrow=open;endFill=0;endSize=10;",                                    # association
            "comp":    "startArrow=diamondThin;startFill=1;startSize=14;endArrow=open;endFill=0;endSize=10;",  # composition
            "aggr":    "startArrow=diamondThin;startFill=0;startSize=14;endArrow=open;endFill=0;endSize=10;",  # aggregation
            "derived": "endArrow=open;endFill=0;endSize=10;dashed=1;",                           # derived / inferred
            "inst":    "endArrow=open;endFill=0;endSize=10;dashed=1;dashPattern=8 8;",           # «instanceOf»
        }
        st = base + kinds[kind]
        if exit: st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry: st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        geo = '<mxGeometry relative="1" as="geometry">'
        if pts:
            geo += "<Array as='points'>" + "".join(f'<mxPoint x="{p[0]}" y="{p[1]}"/>' for p in pts) + "</Array>"
        if lx is not None:
            geo += f'<mxPoint x="{lx}" y="{ly}" as="offset"/>'
        geo += "</mxGeometry>"
        self.cells.append(f'<mxCell id="{eid}" value="{escape(label)}" style="{st}" edge="1" parent="1" '
                          f'source="{src}" target="{tgt}">{geo}</mxCell>')
        return eid

    def xml(self, idx):
        body = "\n        ".join(self.cells)
        return (f'  <diagram id="page{idx}" name="{escape(self.name)}">\n'
                f'    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
                f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" '
                f'math="0" shadow="0">\n      <root>\n        <mxCell id="0"/>\n        '
                f'<mxCell id="1" parent="0"/>\n        {body}\n      </root>\n    </mxGraphModel>\n  </diagram>')


LEGEND = ("<b>Notation</b><br/>"
          "&#9723; grey = imported (EMMO / EMMO-domain)&#160;&#160;"
          "&#9723; white = BattGPT core&#160;&#160;"
          "&#9723; cyan = BattGPT classification vocabulary<br/>"
          "&#9670;&#8212; composition (subPropertyOf emmo:hasPart) &#183; part is per-material and owned by one whole<br/>"
          "&#9671;&#8212; aggregation (subPropertyOf emmo:hasConstituent) &#183; constituent is shared across materials<br/>"
          "&#9651; generalization (rdfs:subClassOf)&#160;&#160;&#8594; association&#160;&#160;"
          "- - &#8594; derived (owl:propertyChainAxiom) / &#171;instanceOf&#187;<br/>"
          "{1..*} = owl:someValuesFrom restriction asserted on the owning class")

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1 — Core class model
# ══════════════════════════════════════════════════════════════════════════
p1 = Page("1 - BattGPT Core Class Model (M1)")
p1.note(40, 8, 900, 30, "<b>BattGPT Ontology &#8212; Core Class Model (M1)</b><br/>"
        "<i>material-centric: emmo:ChemicalSubstance is the hub; every structural class is reached from it</i>", fs=13)

# --- battery role column (left) ---
role_parent = p1.box(40, 70, 210, "emmo:Role", GREY)
battery_role = p1.box(40, 150, 210, "battgpt:BatteryRole", WHITE)
roles = []
for i, r in enumerate(["battgpt:PositiveElectrodeRole", "battgpt:NegativeElectrodeRole",
                       "battgpt:ElectrolyteRole", "battgpt:SeparatorRole"]):
    roles.append(p1.box(40, 240 + i*48, 210, r, CYAN))
p1.edge(battery_role, role_parent, "", "gen", exit=(0.5, 0), entry=(0.5, 1))
for r in roles:
    p1.edge(r, battery_role, "", "gen", exit=(0.5, 0), entry=(0.5, 1))
p1.note(40, 434, 210, 16, "<i>{disjoint}</i>", align="center")

# --- spine (centre) ---
mat = p1.cls(360, 70, 250, "emmo:ChemicalSubstance", [
    "formula: string", "chemsys: string", "materialProjectId: string",
    "isStable: boolean", "isMetal: boolean", "isGapDirect: boolean",
    "isTheoretical: boolean", "smactValidity: boolean"], GREY)
cs  = p1.cls(360, 300, 250, "battgpt:CrystalStructure", ["cif: string", "pointGroup: string"], WHITE)
uc  = p1.cls(360, 420, 250, "battgpt:UnitCell", [
    "latticeA: double (Å)", "latticeB: double (Å)", "latticeC: double (Å)",
    "alpha: double (deg)", "beta: double (deg)", "gamma: double (deg)"], WHITE)
site = p1.cls(360, 600, 250, "battgpt:Site", [
    "fractionalX: double", "fractionalY: double", "fractionalZ: double"], WHITE)
spec = p1.cls(360, 810, 250, "battgpt:Species", ["oxidationState: integer"], WHITE)
elem = p1.cls(360, 910, 250, "emmo:ChemicalElement", [
    "atomicMass: double (u)", "group: integer", "period: integer",
    "electronegativity: double", "covalentRadius: double (Å)", "valenceElectrons: integer"], GREY)

p1.edge(mat,  cs,   "hasStructure {1..*}",  "comp", exit=(0.5, 1), entry=(0.5, 0))
p1.edge(cs,   uc,   "hasUnitCell {1..*}",   "comp", exit=(0.5, 1), entry=(0.5, 0))
p1.edge(uc,   site, "hasSite {1..*}",       "comp", exit=(0.5, 1), entry=(0.5, 0))
p1.edge(site, spec, "hasSpecies {1..*}",    "aggr", exit=(0.3, 1), entry=(0.3, 0))
p1.edge(spec, elem, "hasElement {1..*}",    "aggr", exit=(0.5, 1), entry=(0.5, 0))

# role <-> material  (two separate lanes so the labels do not collide)
# belongsToElectrode: range is owl:unionOf(PositiveElectrodeRole, NegativeElectrodeRole)
#   -> BOTH electrode roles are valid targets; Electrolyte/Separator deliberately are not.
p1.edge(mat, roles[0], "belongsToElectrode", "assoc", exit=(0, 0.10), entry=(1, 0.5),
        pts=[(330, 93), (330, 255)], lx=0, ly=-12)
p1.edge(mat, roles[1], "belongsToElectrode", "assoc", exit=(0, 0.16), entry=(1, 0.5),
        pts=[(310, 107), (310, 303)], lx=0, ly=-12)
p1.note(258, 268, 100, 40, "<i>{range =<br/>Positive &#8746;<br/>Negative}</i>", align="center")
p1.edge(battery_role, mat, "usesMaterial", "assoc", exit=(1, 0.5), entry=(0, 0.66),
        pts=[(290, 165), (290, 220)])
p1.note(30, 462, 230, 44,
        "<i>usesMaterial is declared on the BatteryRole<br/>superclass, so it applies to all four roles;<br/>"
        "belongsToElectrode is restricted to the two electrode roles.</i>")

# --- connectivity cluster (right of Site, clear vertical lanes) ---
bond = p1.cls(760, 700, 260, "battgpt:CrystalBond", [
    "bondDistance: double (Å)", "coordinationMethod: string"], WHITE, stereo="association class")
p1.edge(site, bond, "hasBond", "assoc", exit=(1, 0.35), entry=(0, 0.35), pts=[(690, 626)])
p1.edge(bond, site, "hasSourceSite {1..*}", "assoc", exit=(0, 0.85), entry=(1, 0.85),
        pts=[(660, 762), (660, 664)])
p1.edge(bond, site, "hasTargetSite {1..*}", "assoc", exit=(0.5, 1), entry=(0.75, 1),
        pts=[(890, 790), (548, 790)])
p1.edge(site, site, "/hasBondTo  «derived»", "derived", exit=(0.08, 1), entry=(0.02, 1),
        pts=[(380, 700), (365, 700)])

# --- classification column (right) ---
prop_parent = p1.box(1080, 70, 250, "emmo:Property", GREY)
sg  = p1.cls(1080, 150, 250, "battgpt:SpaceGroup",
             ["symmetrySymbol: string", "spaceGroupNumber: integer"], CYAN)
csy = p1.box(1080, 270, 250, "battgpt:CrystalSystem", CYAN)
sf  = p1.box(1080, 340, 250, "battgpt:StructureFamily", CYAN)
cg  = p1.box(1080, 410, 250, "battgpt:CoordinationGeometry", CYAN)
for c in (sg, csy, sf, cg):
    p1.edge(c, prop_parent, "", "gen", exit=(0.5, 0), entry=(0.5, 1))
p1.edge(cs, sg,  "hasSpaceGroup {1..*}", "assoc", exit=(1, 0.25), entry=(0, 0.5), pts=[(1040, 318)])
p1.edge(cs, csy, "hasCrystalSystem",     "assoc", exit=(1, 0.6),  entry=(0, 0.5), pts=[(1010, 348)])
p1.edge(cs, sf,  "hasStructureFamily",   "assoc", exit=(1, 0.9),  entry=(0, 0.5), pts=[(980, 372)])
p1.edge(site, cg, "hasCoordinationGeometry", "assoc", exit=(1, 0.12), entry=(0, 0.5),
        pts=[(1050, 618), (1050, 425)])

p1.note(1080, 470, 250, 46,
        "<i>Quantitative properties (band gap, formation<br/>energy, moduli, cell-level electrochemistry):<br/>see Fig. 2</i>")
p1.legend(1080, 560, 480, 130, LEGEND)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 2 — Quantity / property model
# ══════════════════════════════════════════════════════════════════════════
p2 = Page("2 - Quantitative Property Model")
p2.note(40, 8, 1000, 30, "<b>BattGPT &#8212; Quantitative Property Model</b><br/>"
        "<i>every quantity is a reified property node, never a bare literal on the material; "
        "all links below are rdfs:subPropertyOf emmo:hasProperty</i>", fs=13)

e_prop = p2.box(720, 70, 200, "emmo:Property", GREY)
e_en   = p2.box(500, 150, 200, "emmo:Energy", GREY)
e_pr   = p2.box(730, 150, 200, "emmo:Pressure", GREY)
e_vo   = p2.box(960, 150, 200, "emmo:Voltage", GREY)
for c in (e_en, e_pr, e_vo):
    p2.edge(c, e_prop, "", "gen", exit=(0.5, 0), entry=(0.5, 1))

mat2 = p2.box(60, 250, 240, "emmo:ChemicalSubstance", GREY, h=280)
props = [("battgpt:BandGapProperty", e_en, "hasBandGap"),
         ("battgpt:FormationEnergyProperty", e_en, "hasFormationEnergy"),
         ("battgpt:EnergyAboveHullProperty", e_en, "hasEnergyAboveHull"),
         ("battgpt:BulkModulusProperty", e_pr, "hasBulkModulus"),
         ("battgpt:ShearModulusProperty", e_pr, "hasShearModulus")]
for i, (nm, parent, lbl) in enumerate(props):
    y = 250 + i*56
    bx = p2.box(470, y, 280, nm, WHITE)
    p2.edge(bx, parent, "", "gen", exit=(1, 0.5), entry=(0.5, 1),
            pts=[(800 + i*22, y + 15), (800 + i*22, 200)])
    p2.edge(mat2, bx, lbl, "assoc", exit=(1, (i*56 + 15) / 280.0), entry=(0, 0.5),
            pts=[(400, y + 15)])

p2.legend(1020, 300, 420, 90,
          "<b>Reading a property node</b><br/>"
          "material &#8212;hasBandGap&#8594; :BandGapProperty<br/>"
          "&#160;&#160;&#160;&#160;&#8226; emmo:hasNumberValue &#8594; 3.9224<br/>"
          "&#160;&#160;&#160;&#160;&#8226; emmo:hasMeasurementUnit &#8594; unit:EV")

# --- cell-level electrochemistry: tall hub so the eight labels never stack ---
cell = p2.box(60, 620, 240, "battery:BatteryCell", GREY, h=376)
ec = [("electro:Capacity", "hasCapacity"), ("electro:SpecificCapacity", "hasSpecificCapacity"),
      ("electro:IonicConductivity", "hasIonicConductivity"), ("electro:OpenCircuitVoltage", "hasOpenCircuitVoltage"),
      ("electro:CRate", "hasCRate"), ("electro:CoulombicEfficiency", "hasCoulombicEfficiency"),
      ("electro:StateOfCharge", "hasStateOfCharge"), ("emmo:Voltage", "hasVoltage")]
for i, (cn, lbl) in enumerate(ec):
    y = 620 + i*47
    bx = p2.box(470, y, 280, cn, GREY)
    p2.edge(cell, bx, lbl, "assoc", exit=(1, (i*47 + 15) / 376.0), entry=(0, 0.5))
p2.note(60, 1020, 400, 70,
        "<i>battery:BatteryCell and every electro: range class are reused from<br/>"
        "EMMO domain-battery 0.20.2 / domain-electrochemistry 0.37.2 &#8212;<br/>"
        "not redefined here. Only the eight has* predicates are BattGPT's.</i>")

# ══════════════════════════════════════════════════════════════════════════
# PAGE 3 — Classification taxonomy + enumerated individuals
# ══════════════════════════════════════════════════════════════════════════
p3 = Page("3 - Classification Taxonomy and Individuals")
p3.note(40, 8, 1100, 30, "<b>BattGPT &#8212; Classification Vocabulary</b><br/>"
        "<i>closed vocabularies: each leaf class has exactly one canonical owl:NamedIndividual, "
        "asserted owl:AllDifferent; sibling classes asserted owl:AllDisjointClasses</i>", fs=13)

sf3 = p3.box(560, 70, 220, "battgpt:StructureFamily", CYAN)
ox  = p3.box(230, 160, 210, "battgpt:OxideStructureFamily", CYAN)
po  = p3.box(460, 160, 210, "battgpt:PolyanionStructureFamily", CYAN)
su  = p3.box(690, 160, 210, "battgpt:SulfideStructureFamily", CYAN)
gar = p3.box(920, 160, 210, "battgpt:GarnetStructure", CYAN)
per = p3.box(1150, 160, 210, "battgpt:PerovskiteStructure", CYAN)
for c in (ox, po, su, gar, per):
    p3.edge(c, sf3, "", "gen", exit=(0.5, 0), entry=(0.5, 1))
p3.note(560, 118, 220, 16, "<i>{disjoint}</i>", align="center")

leaves = [("battgpt:LayeredOxideStructure", ox), ("battgpt:SpinelStructure", ox),
          ("battgpt:RockSaltStructure", ox), ("battgpt:OlivineStructure", po),
          ("battgpt:NASICONStructure", po), ("battgpt:LGPSTypeStructure", su),
          ("battgpt:ArgyroditeStructure", su)]
col = {ox: 230, po: 460, su: 690}
cnt = {ox: 0, po: 0, su: 0}
leafbox = {}
for nm, par in leaves:
    y = 250 + cnt[par]*52
    cnt[par] += 1
    b = p3.box(col[par], y, 210, nm, CYAN)
    leafbox[nm] = b
    p3.edge(b, par, "", "gen", exit=(0.5, 0), entry=(0.5, 1))
leafbox["battgpt:GarnetStructure"] = gar
leafbox["battgpt:PerovskiteStructure"] = per
p3.note(230, 412, 440, 16, "<i>all nine leaf classes: {disjoint}</i>", align="center")

# canonical individuals
p3.note(40, 470, 400, 20, "<b>Canonical individuals (owl:AllDifferent)</b>", fs=11)
inds = ["LayeredOxideStructureIndividual", "SpinelStructureIndividual", "RockSaltStructureIndividual",
        "OlivineStructureIndividual", "NASICONStructureIndividual", "GarnetStructureIndividual",
        "PerovskiteStructureIndividual", "LGPSTypeStructureIndividual", "ArgyroditeStructureIndividual"]
for i, nm in enumerate(inds):
    p3.box(40 + (i % 3)*310, 500 + (i // 3)*44, 300, nm + " : StructureFamily", PINK, bold=False, underline=True, fs=10)

# coordination geometry + roles
cg3 = p3.box(1000, 470, 260, "battgpt:CoordinationGeometry", CYAN)
p3.note(1000, 505, 260, 130,
        "<i>8 canonical individuals (owl:AllDifferent):</i><br/>"
        "Linear &#183; TrigonalPlanar &#183; Tetrahedral &#183;<br/>SquarePyramidal &#183; Octahedral &#183;<br/>"
        "PentagonalBipyramidal &#183;<br/>SquareAntiprismatic &#183; Cuboctahedral")
br3 = p3.box(1000, 650, 260, "battgpt:BatteryRole", CYAN)
p3.note(1000, 685, 260, 90,
        "<i>4 canonical individuals (owl:AllDifferent):</i><br/>"
        "PositiveElectrodeRoleIndividual &#183;<br/>NegativeElectrodeRoleIndividual &#183;<br/>"
        "ElectrolyteRoleIndividual &#183; SeparatorRoleIndividual")

# ══════════════════════════════════════════════════════════════════════════
# PAGE 4 — M0 instance model (real data: LiFePO4, mp-19017)
# ══════════════════════════════════════════════════════════════════════════
p4 = Page("4 - M0 Instance Model (LiFePO4, mp-19017)")
p4.note(40, 8, 1100, 34, "<b>BattGPT M0 Instance Model &#8212; LiFePO&#8324; (mp-19017)</b><br/>"
        "<i>values taken verbatim from the generated knowledge graph; "
        "dashed &#171;instanceOf&#187; links point to the M1 classes of Fig. 1</i>", fs=13)

m1_mat  = p4.box(60, 70, 220, "emmo:ChemicalSubstance", GREY)
m1_cs   = p4.box(340, 70, 200, "battgpt:CrystalStructure", WHITE)
m1_uc   = p4.box(600, 70, 180, "battgpt:UnitCell", WHITE)
m1_site = p4.box(840, 70, 160, "battgpt:Site", WHITE)
m1_bond = p4.box(1060, 70, 200, "battgpt:CrystalBond", WHITE)

i_mat = p4.cls(60, 190, 240, "mp-19017 : ChemicalSubstance", [
    "formula = \"LiFePO4\"", "chemsys = \"Fe-Li-O-P\"",
    "isStable = true", "isMetal = false"], PINK)
i_cs = p4.cls(340, 190, 220, "crystal_mp-19017 : CrystalStructure", ["pointGroup = \"mmm\""], PINK)
i_uc = p4.cls(600, 190, 220, "unitcell_mp-19017 : UnitCell", [
    "latticeA = 10.236", "latticeB = 5.971", "latticeC = 4.655",
    "alpha = beta = gamma = 90.0"], PINK)
i_site = p4.cls(880, 190, 220, "site_4 : Site", [
    "fractionalX = 0.7812", "fractionalY = 0.2500", "fractionalZ = 0.5299"], PINK)
i_bond = p4.cls(1160, 190, 230, "bond_4_13 : CrystalBond", [
    "bondDistance = 2.035", "coordinationMethod = \"CrystalNN\""], PINK)
i_site13 = p4.box(1160, 330, 230, "site_13 : Site", PINK, bold=False, underline=True, fs=10)

p4.edge(i_mat,  m1_mat,  "«instanceOf»", "inst", exit=(0.5, 0), entry=(0.5, 1))
p4.edge(i_cs,   m1_cs,   "«instanceOf»", "inst", exit=(0.5, 0), entry=(0.5, 1))
p4.edge(i_uc,   m1_uc,   "«instanceOf»", "inst", exit=(0.5, 0), entry=(0.5, 1))
p4.edge(i_site, m1_site, "«instanceOf»", "inst", exit=(0.5, 0), entry=(0.5, 1))
p4.edge(i_bond, m1_bond, "«instanceOf»", "inst", exit=(0.5, 0), entry=(0.5, 1))

p4.edge(i_mat,  i_cs,   "hasStructure",  "comp", exit=(1, 0.5), entry=(0, 0.5))
p4.edge(i_cs,   i_uc,   "hasUnitCell",   "comp", exit=(1, 0.5), entry=(0, 0.5))
p4.edge(i_uc,   i_site, "hasSite",       "comp", exit=(1, 0.5), entry=(0, 0.5))
p4.edge(i_site, i_bond, "hasBond",       "assoc", exit=(1, 0.5), entry=(0, 0.5))
p4.edge(i_bond, i_site13, "hasTargetSite", "assoc", exit=(0.5, 1), entry=(0.5, 0))
p4.edge(i_bond, i_site, "hasSourceSite", "assoc", exit=(0, 0.85), entry=(1, 0.85))

i_spec = p4.box(880, 400, 220, "Fe : Species", PINK, bold=False, underline=True, fs=10)
i_elem = p4.cls(880, 470, 220, "Fe : ChemicalElement", [
    "atomicMass = 55.845", "electronegativity = 1.83"], PINK)
p4.edge(i_site, i_spec, "hasSpecies", "aggr", exit=(0.5, 1), entry=(0.5, 0))
p4.edge(i_spec, i_elem, "hasElement", "aggr", exit=(0.5, 1), entry=(0.5, 0))

i_geo = p4.box(600, 400, 240, "OctahedralGeometryIndividual", CYAN, bold=False, fs=10)
p4.edge(i_site, i_geo, "hasCoordinationGeometry", "assoc", exit=(0, 0.5), entry=(1, 0.5))
i_sg = p4.cls(340, 420, 220, "SpaceGroup_62 : SpaceGroup", [
    "symmetrySymbol = \"Pnma\"", "spaceGroupNumber = 62"], PINK)
p4.edge(i_cs, i_sg, "hasSpaceGroup", "assoc", exit=(0.5, 1), entry=(0.5, 0))
i_fam = p4.box(600, 330, 240, "OlivineStructureIndividual", CYAN, bold=False, fs=10)
p4.edge(i_cs, i_fam, "hasStructureFamily", "assoc", exit=(1, 0.75), entry=(0, 0.5))

i_role = p4.box(60, 400, 240, "PositiveElectrodeRoleIndividual", CYAN, bold=False, fs=10)
p4.edge(i_mat, i_role, "belongsToElectrode", "assoc", exit=(0.5, 1), entry=(0.5, 0))

i_bandgap = p4.cls(60, 480, 240, "bandgap_mp-19017 : BandGapProperty", [
    "hasNumberValue = 3.9224", "hasMeasurementUnit = unit:EV"], PINK)
p4.edge(i_mat, i_bandgap, "hasBandGap", "assoc", exit=(0, 0.5), entry=(0, 0.5),
        pts=[(30, 250), (30, 505)])

i_cell = p4.cls(60, 600, 240, "cell_mp-19017 : battery:BatteryCell", [], PINK)
i_ocv = p4.cls(340, 590, 250, "ocv : OpenCircuitVoltage", [
    "hasNumberValue = 3.4992", "hasMeasurementUnit = unit:V"], PINK)
i_cap = p4.cls(340, 690, 250, "capacity : SpecificCapacity", [
    "hasNumberValue = 169.89", "hasMeasurementUnit = unit:MilliA-HR-PER-GM"], PINK)
p4.edge(i_cell, i_ocv, "hasOpenCircuitVoltage", "assoc", exit=(1, 0.35), entry=(0, 0.5), lx=30, ly=-12)
p4.edge(i_cell, i_cap, "hasSpecificCapacity",  "assoc", exit=(1, 0.85), entry=(0, 0.5), lx=30, ly=-12)
p4.note(60, 690, 240, 60, "<i>the cell is linked to its active material<br/>by dcterms:relation "
        "(cell-level quantities are<br/>not properties of the material itself)</i>")

pages = [p1, p2, p3, p4]
out = ('<mxfile host="app.diagrams.net" agent="battgpt-uml-generator" version="27.0.9" '
       f'pages="{len(pages)}">\n' + "\n".join(p.xml(i+1) for i, p in enumerate(pages)) + "\n</mxfile>\n")
open("/Users/shantharam/FYP/battGPT/BattGpt-Ontology/UML_BattGPT_v0.3.2.drawio", "w").write(out)
print("written:", sum(len(p.cells) for p in pages), "cells across", len(pages), "pages")
