from asyncore import read
import xlrd
from scipy.optimize import linprog
from .models import FileResult
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from datetime import datetime
import io
from django.core.files import File
from pulp import *
import math


# returns a dictionary with key the name of the cell and value a list which contains the rows of the cell
def getFileColumns(file_path):
    data = {}
    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheet_by_index(0)
    for i in range(1, sheet.ncols):
        arrayofvalues = sheet.col_values(i)
        data[arrayofvalues[0]] = []
        for x, i in enumerate(arrayofvalues):
            if x > 0:
                data[arrayofvalues[0]].append(i)
    return data


# returns a dictionary with key the name of the row and value a list which contains the cells of the row
def getFileRows(file_path):
    data = {}
    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheet_by_index(0)
    for i in range(1, sheet.nrows):
        arrayofvalues = sheet.row_values(i)
        data[arrayofvalues[0]] = []
        for x, i in enumerate(arrayofvalues):
            if x > 0:
                data[arrayofvalues[0]].append(i)
    return data


def pulp_solve(file, inputs, outputs, minmax, rts):
    ten_8 = 1 / math.pow(10, 8)
    columns = getFileColumns(file.file.path)
    rows = getFileRows(file.file.path)
    results = {}
    objective_values = {}
    eff_ratios = {}
    # create problem
    if minmax == "Max":
        # input orientation: MM problem is max
        orientation = LpMaximize
    else:
        # output orientation: MM problem is min
        orientation = LpMinimize
    problem_name = str(file.name)
    problem_name = problem_name.replace(" ", "_")

    # for each row (DMU)
    for (index, row) in enumerate(rows):
        problem = LpProblem(problem_name, orientation)
        row_vars = []
        input_obj = []
        output_obj = []
        # print("DMU " + str(index) + " is " + str(row))
        # for each column (variable)
        for col in columns:
            col_name = col.replace(" ", "_")
            # print("column " + str(col_name) + " = " + str(columns[col][index]))
            # define the variables
            col_name = LpVariable(name=col_name, lowBound=0)
            # append var in list
            row_vars.append(col_name)
            # append the variable with its value in inputs or outputs
            if col in inputs:
                input_obj.append(int(columns[col][index]) * col_name)
            elif col in outputs:
                output_obj.append(int(columns[col][index]) * col_name)
        # for vrs add extra variable
        if rts == "vrs":
            v_zero = LpVariable(name="var_zero")

        if minmax == 'Min':
            eq_constraint = LpConstraint(lpSum(output_obj), sense=LpConstraintEQ, rhs=1, name="equality constraint")
            # problem.addConstraint(LpConstraint(lpSum(output_obj), sense=LpConstraintEQ, rhs=1, name="equality constraint"))
            # if vrs add extra variable
            if rts == "vrs":
                input_obj.append(v_zero * (-1))
            # if output oriented then build objective function with inputs (min inputs)
            obj = lpSum(input_obj)
        elif minmax == 'Max':
            eq_constraint = LpConstraint(lpSum(input_obj), sense=LpConstraintEQ, rhs=1, name="equality constraint")
            # problem.addConstraint(LpConstraint(lpSum(input_obj), sense=LpConstraintEQ, rhs=1, name="equality constraint"))
            # if vrs add extra variable
            if rts == "vrs":
                output_obj.append(v_zero * (-1))
            # if input oriented then build objective function with outputs (max outputs)
            obj = lpSum(output_obj)

        # print(obj)
        problem += obj
        # add constraints after objective function in the problem
        problem.addConstraint(eq_constraint)

        # build inequality constraints
        for (row_index, row_name) in enumerate(rows):
            constraint_row_inputs = []
            constraint_row_outputs = []
            c_index = "c_" + str(row_index)
            # print(c_index)
            for (col_index, col) in enumerate(columns):
                if col in inputs:
                    constraint_row_inputs.append(int(columns[col][row_index]) * row_vars[col_index])
                elif col in outputs:
                    constraint_row_outputs.append(int(columns[col][row_index]) * row_vars[col_index])
            if rts == "vrs" and minmax == "Min":
                constraint = lpSum(constraint_row_inputs) - lpSum(constraint_row_outputs) - v_zero
            elif rts == "vrs" and minmax == "Max":
                constraint = lpSum(constraint_row_inputs) - lpSum(constraint_row_outputs) + v_zero
            else:
                constraint = lpSum(constraint_row_inputs) - lpSum(constraint_row_outputs)
            problem.addConstraint(LpConstraint(e=constraint, sense=LpConstraintGE, name=c_index, rhs=0))
            # print("---constraints----")
            # print(constraint)

        problem.solve(PULP_CBC_CMD(mip=False))
        results[row] = problem
        objective_value = round(problem.objective.value(), 4)
        objective_values[row] = objective_value
        # calculate efficiency ratios %
        if minmax == 'Min':
            # minimization problem, so eff = 1/obj
            eff_ratio = (1 / objective_value) * 100
        else:
            eff_ratio = objective_value * 100
        eff_ratios[row] = round(eff_ratio, 4)

    # analysis details dict
    analysis = {'orientation': minmax, 'rts': rts, 'inputs': inputs, 'outputs': outputs}

    # calculate efficiency projections
    projections = calculate_projections(results, minmax, objective_values, rows, columns, inputs, outputs)

    # results
    result_data = {
        "details": analysis,
        "results": results,
        "obj_values": objective_values,
        "eff_ratios": eff_ratios,
        "projections": projections
    }

    # create and save results in file
    result_file = save_results_file(file, result_data)

    return result_data


def calculate_projections(results, minmax, obj_values, rows, columns, inputs, outputs):
    l_dict = {}
    l_dict_lists = {}
    projection_values = {}
    projection_sums = {}

    # for each DMU
    for row, result in results.items():
        c_dict = {}
        l_list = []
        # if DMU is inefficient
        if obj_values[row] != 1.0:
            for name, constraint in result.constraints.items():
                # skip first constraint
                if name != 'equality_constraint':
                    c_dict[name] = constraint.pi
                    l_list.append(constraint.pi)

            l_dict[row] = c_dict
            l_dict_lists[row] = l_list

    rows_list = list(rows.values())

    for dmu, l_items in l_dict_lists.items():
        col_lists = []
        for col in columns:
            col_lists.append([])

        for (item_index, l_item) in enumerate(l_items):
            for (col_index, col) in enumerate(columns):
                col_value = l_item * columns[col][item_index]
                col_lists[col_index].append(col_value)

        projection_values[dmu] = col_lists

    for row, result in projection_values.items():
        projection_sums_list = []
        for (col_index, col) in enumerate(columns):
            projection_sums_list.append(sum(result[col_index]))
        projection_sums[row] = projection_sums_list

    columns_list = []
    for col in columns:
        columns_list.append(col)
    projection_sums["cols"] = columns_list
    # print(projection_sums)
    return projection_sums


def save_results_file(file, result_data):
    # build pdf data
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18,
                            author='Django DEA App')
    doc.title = "DEA results"
    Story = []
    styles = getSampleStyleSheet()
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Results for " + file.name, styles['Title']))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph(datetime.today().strftime('%d/%m/%Y'), styles["Normal"]))
    Story.append(Spacer(1, 12))
    if result_data["details"]["orientation"] == 'Max':
        orientation = "Input"
    else:
        orientation = "Output"
    Story.append(Paragraph('Orientation: ' + orientation, styles["Normal"]))
    Story.append(Spacer(1, 12))
    if result_data["details"]["rts"] == 'crs':
        rts = 'Constant'
    else:
        rts = 'Variable'
    Story.append(Paragraph('Returns to Scale: ' + rts, styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Inputs", styles["Heading2"]))
    Story.append(Spacer(1, 12))
    for input in result_data["details"]["inputs"]:
        Story.append(Paragraph(input, styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Outputs", styles["Heading2"]))
    Story.append(Spacer(1, 12))
    for output in result_data["details"]["outputs"]:
        Story.append(Paragraph(output, styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Analysis results", styles["Heading1"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Objective function values and efficiency ratios %", styles["Heading2"]))
    Story.append(Spacer(1, 12))
    for obj, value in result_data["obj_values"].items():
        Story.append(Paragraph("For DMU " + str(obj) + ": Obj. Func. = " + str(value) + "  |  Efficiency = " + str(result_data["eff_ratios"][obj]) + " %", styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Efficiency Projections", styles["Heading2"]))
    Story.append(Spacer(1, 12))
    for obj, projections in result_data["projections"].items():
        if obj != 'cols':
            Story.append(Paragraph("For DMU " + str(obj), styles["Heading3"]))
            for index, col in enumerate(result_data["projections"]["cols"]):
                Story.append(Paragraph(col + " = " + str(projections[index]), styles["Normal"]))
            Story.append(Spacer(1, 12))
    Story.append(Spacer(1, 12))
    # Story.append(Paragraph("Linear Problems", styles["Heading2"]))
    # Story.append(Spacer(1, 12))
    # for dmu, result in result_data["results"].items():
    #     Story.append(Paragraph("DMU: " + dmu, styles["Heading3"]))
    #     Story.append(Spacer(1, 12))
    #     Story.append(Paragraph(str(result), styles["Normal"]))
    doc.build(Story)
    buffer.seek(0)
    pdf_file = File(buffer, name=file.name + "_results.pdf")

    # insert in FileResult class
    file_results = FileResult(file=file, results_file=pdf_file)
    file_results.save()
    return file_results
