import os
import sys
import math
import win32com.client
import pythoncom
import comtypes.client


def clockwise_angle_and_distance(point, origin, ref_vec=[1, 0]):
    vector = [point[0] - origin[0], point[1] - origin[1]]
    len_vector = math.hypot(vector[0], vector[1])
    if len_vector == 0:
        return -math.pi, 0
    normalized = [vector[0] / len_vector, vector[1] / len_vector]
    dot_prod = normalized[0] * ref_vec[0] + normalized[1] * ref_vec[1]
    diff_prod = ref_vec[1] * normalized[0] - ref_vec[0] * normalized[1]
    angle = math.atan2(diff_prod, dot_prod)
    if angle < 0:
        return 2 * math.pi + angle, len_vector
    return angle, len_vector


class CAD:
    def __init__(self):
        self.acad = win32com.client.Dispatch("AutoCAD.Application")
        self.acadModel = self.acad.ActiveDocument.ModelSpace


def convert_units(Units):
    if isinstance(Units, int):
        if 1 <= Units <= 16:
            return Units
        else:
            return None
    if Units == "lb_in_F":
        Units = 1
    elif Units == "lb_ft_F":
        Units = 2
    elif Units == "kip_in_F":
        Units = 3
    elif Units == "kip_ft_F":
        Units = 4
    elif Units == "kN_mm_C":
        Units = 5
    elif Units == "kN_m_C":
        Units = 6
    elif Units == "kgf_mm_C":
        Units = 7
    elif Units == "kgf_m_C":
        Units = 8
    elif Units == "N_mm_C":
        Units = 9
    elif Units == "N_m_C":
        Units = 10
    elif Units == "tonf_mm_C":
        Units = 11
    elif Units == "tonf_m_C":
        Units = 12
    elif Units == "kN_cm_C":
        Units = 13
    elif Units == "kgf_cm_C":
        Units = 14
    elif Units == "N_cm_C":
        Units = 15
    elif Units == "tonf_cm_C":
        Units = 16
    else:
        Units = None
    return Units


def convert_material_type(MatType):
    if isinstance(MatType, int):
        if 1 <= MatType <= 8:
            return MatType
        else:
            return None
    if MatType == "Steel":
        MatType = 1
    elif MatType == "Concrete":
        MatType = 2
    elif MatType == "NoDesign":
        MatType = 3
    elif MatType == "Aluminum":
        MatType = 4
    elif MatType == "ColdFormed":
        MatType = 5
    elif MatType == "Rebar":
        MatType = 6
    elif MatType == "Tendon":
        MatType = 7
    elif MatType == "Masonry":
        MatType = 8
    else:
        MatType = None
    return MatType


def convert_load_pattern_type(MyType):
    if isinstance(MyType, int):
        if 1 <= MyType <= 12:
            return MyType
        else:
            return None
    if MyType == "Dead":
        MyType = 1
    elif MyType == "SuperDead":
        MyType = 2
    elif MyType == "Live":
        MyType = 3
    elif MyType == "ReduceLive":
        MyType = 4
    elif MyType == "Quake":
        MyType = 5
    elif MyType == "Wind":
        MyType = 6
    elif MyType == "Snow":
        MyType = 7
    elif MyType == "Other":
        MyType = 8
    elif MyType == "Move":
        MyType = 9
    elif MyType == "Temperature":
        MyType = 10
    elif MyType == "RoofLive":
        MyType = 11
    elif MyType == "Notional":
        MyType = 12
    else:
        MyType = None
    return MyType


def convert_direction(Dir):
    if isinstance(Dir, int):
        if 1 <= Dir <= 11:
            return Dir
        else:
            return None
    if Dir == "Local 1":
        Dir = 1
    elif Dir == "Local 2":
        Dir = 2
    elif Dir == "Local 3":
        Dir = 3
    elif Dir == "X":
        Dir = 4
    elif Dir == "Y":
        Dir = 5
    elif Dir == "Z":
        Dir = 6
    elif Dir == "Projected X":
        Dir = 7
    elif Dir == "Projected Y":
        Dir = 8
    elif Dir == "Projected Z":
        Dir = 9
    elif Dir == "Gravity":
        Dir = 10
    elif Dir == "Projected Gravity":
        Dir = 11
    else:
        Dir = None
    return Dir


def validate_coordinate_system(Dir, CSys):
    if Dir in [1, 2, 3] and CSys == "Local":
        return True
    elif Dir in [4, 5, 6, 7, 8, 9] and CSys != "Local":
        return True
    elif Dir in [10, 11] and CSys == "Global":
        return True
    else:
        return False


class SAP:
    def __init__(self):
        self.AttachToInstance = True
        self.SpecifyPath = True
        self.ProgramPath = "C:\Program Files\Computers and Structures\ETABS 20"
        self.APIPath = "D:\PROYECTOS\PROGRAMACION\CSIBotModels"
        if not os.path.exists(self.APIPath):
            try:
                os.makedirs(self.APIPath)
            except OSError:
                pass
        self.ModelPath = self.APIPath + os.sep + 'API_1-001.edb'
        self.helper = comtypes.client.CreateObject('ETABSv1.Helper')
        self.helper = self.helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
        if self.AttachToInstance:
            try:
                self.Etabs = self.helper.GetObject("CSI.ETABS.API.ETABSObject")
            except (OSError, comtypes.COMError):
                print("No running instance of the program found or failed to attach.")
                sys.exit(-1)
        else:
            if self.SpecifyPath:
                try:
                    self.Etabs = self.helper.CreateObject(self.ProgramPath)
                except (OSError, comtypes.COMError):
                    print("Cannot start a new instance of the program from " + self.ProgramPath)
                    sys.exit(-1)
            else:
                try:
                    self.Etabs = self.helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
                except (OSError, comtypes.COMError):
                    print("Cannot start a new instance of the program.")
                    sys.exit(-1)
            self.Etabs.ApplicationStart()
        self.SapModel = self.Etabs.SapModel

    def initialize(self, Units="tonf_m_C"):
        Units = convert_units(Units)
        if Units is None:
            raise Exception("Not recognized units")
        return self.SapModel.InitializeNewModel(Units)

    def new_model(self, temp, *args):
        if args is None:
            args = [3, 3, 3, 4, 4, 5, 5]
        if temp == 1:
            ret = self.SapModel.File.NewBlank()
        elif temp == 2:
            ret = self.SapModel.File.NewGridOnly(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
        elif temp == 3:
            ret = self.SapModel.File.NewSteelDeck(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
        else:
            raise Exception("Not available template option")
        return ret

    def save_model(self):
        return self.SapModel.File.Save(self.ModelPath)

    def run_analysis(self):
        return self.SapModel.Analyze.RunAnalysis()

    def switch_units(self, Units="tonf_m_C"):
        Units = convert_units(Units)
        if Units is None:
            return
        return self.SapModel.SetPresentUnits(Units)

    def define_material(self, Name: str, MatType, E, U, A, Temp=0):
        MatType = convert_material_type(MatType)
        if MatType is None:
            return
        self.SapModel.PropMaterial.SetMaterial(Name, MatType)
        return self.SapModel.PropMaterial.SetMPIsotropic(Name, E, U, A, Temp)

    def define_rectangular_frame_section(self, Name: str, MatProp: str, T3: float, T2: float,
                                         A=1, V2=1, V3=1, T=1, M2=1, M3=1, Mm=1, Wm=1):
        self.SapModel.PropFrame.SetRectangle(Name, MatProp, T3, T2)
        Value = [A, V2, V3, T, M2, M3, Mm, Wm]
        return self.SapModel.PropFrame.SetModifiers(Name, Value)

    def define_load_pattern(self, Name: str, MyType, SelfWTMultiplier=0, AddAnalysisCase=True):
        MyType = convert_load_pattern_type(MyType)
        if MyType is None:
            return
        return self.SapModel.LoadPatterns.Add(Name, MyType, SelfWTMultiplier, AddAnalysisCase)

    def draw_frame(self, I_coord: list, J_coord: list, PropName="Default", UserName="", CSys="Global"):
        Name = ""
        XI, YI, ZI = I_coord[0], I_coord[1], I_coord[2]
        XJ, YJ, ZJ = J_coord[0], J_coord[1], J_coord[2]
        return self.SapModel.FrameObj.AddByCoord(XI, YI, ZI, XJ, YJ, ZJ, Name, PropName, UserName, CSys)

    def get_points(self, frameName):
        pointName1 = ""
        pointName2 = ""
        return self.SapModel.FrameObj.GetPoints(frameName, pointName1, pointName2)

    def get_releases(self, frameName):
        II, JJ, StartValue, EndValue = [], [], [], []
        return self.SapModel.FrameObj.GetReleases(frameName, II, JJ, StartValue, EndValue)

    def get_loads_distributed(self, Name, ItemType=0):
        NumberItems, FrameName, LoadPat, MyType, CSys, Dir, RD1, RD2 = 0, [], [], [], [], [], [], []
        Dist1, Dist2, Val1, Val2 = [], [], [], []
        return self.SapModel.FrameObj.GetLoadDistributed(Name, NumberItems, FrameName, LoadPat, MyType, CSys, Dir,
                                                         RD1, RD2, Dist1, Dist2, Val1, Val2, ItemType)

    def assign_restraints(self, pointName, U1=False, U2=False, U3=False, R1=False, R2=False, R3=False, itemType=0):
        restraints = [U1, U2, U3, R1, R2, R3]
        return self.SapModel.PointObj.SetRestraint(pointName, restraints, itemType)

    def assign_point_load(self, pointName, patternName, F1=0, F2=0, F3=0, M1=0, M2=0, M3=0, replace=False, CSys="Global"
                          , itemType=0):
        forces = [F1, F2, F3, M1, M2, M3]
        return self.SapModel.PointObj.SetLoadForce(pointName, patternName, forces, replace, CSys, itemType)

    def assign_frame_dist_load(self, frameName, patternName, dist1, dist2, val1, val2, Dir="Gravity", eType=1,
                               relDist=False, replace=False, CSys="Global", itemType=0):
        Dir = convert_direction(Dir)
        if Dir is None:
            return
        if validate_coordinate_system(Dir, CSys):
            return self.SapModel.FrameObj.SetLoadDistributed(frameName, patternName, eType, Dir, dist1, dist2, val1,
                                                             val2, CSys, relDist, replace, itemType)

    def draw_area(self, coordList, propName="Default", userName="", CSys="Global"):
        numPoints = len(coordList)
        XList = []
        YList = []
        ZList = []
        for coord in coordList:
            XList.append(coord[0])
            YList.append(coord[1])
            ZList.append(coord[2])
        areaName = " "
        return self.SapModel.AreaObj.AddByCoord(numPoints, XList, YList, ZList, areaName, propName, userName, CSys)

    def draw_area_by_point(self, pointNamesList, propName="Default", userName=""):
        numPoints = len(pointNamesList)
        areaName = " "
        return self.SapModel.AreaObj.AddByPoint(numPoints, pointNamesList, areaName, propName, userName)

    def refresh_view(self, num=0, zoom=True):
        return self.SapModel.View.RefreshView(num, zoom)


if __name__ == "__main__":
    etabs = SAP()
    # etabs.initialize(6)
    # etabs.new_model(1)
    print(etabs.get_releases("1"))
    print(etabs.get_loads_distributed("1"))
    # print(etabs.draw_frame([2, 2, 0], [3, 5, 0]))
    # print(etabs.draw_frame([0, 1, 0], [2, 10, 0]))
    # print(etabs.draw_area([[0, 0, 0], [1, 0, 0], [1, 3, 0], [0, 3, 0]]))
    # pts = [[2,3], [5,2],[4,1],[3.5,1],[1,2],[2,1],[3,1],[3,3],[4,3]]
    # sort = sorted(pts, key=clockwise_angle_and_distance)
    # print(sort)
