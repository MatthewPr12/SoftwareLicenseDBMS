from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
import datetime

templates = Jinja2Templates(directory="templates")
app = FastAPI()

# Establish a connection to the database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="SoftwareLicense3"
)

# Create a cursor to execute SQL queries
cursor = db.cursor()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def execute_query(request: Request, query: str = Form(...)):
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        headers = [i[0] for i in cursor.description]
        rows = [dict(zip(headers, row)) for row in result]
        return """
            <html>
                <head>
                    <title>Query Results</title>
                </head>
                <body>
                    <h1>Query Results:</h1>
                    <table>
                        <thead>
                            <tr>""" + \
               "".join(["<th>{}</th>".format(header) for header in headers]) + \
               """</tr>
           </thead>
           <tbody>""" + \
               "".join(["<tr>" + "".join(["<td>{}</td>".format(row[field]) for field in headers]) + "</tr>" for row in
                        rows]) + \
               """</tbody>
       </table>
       <br>
       <a href="/">Execute Another Query</a>
   </body>
</html>
"""
    except mysql.connector.Error as error:
        return """
            <html>
                <head>
                    <title>Error</title>
                </head>
                <body>
                    <h1>Error:</h1>
                    <p>{}</p>
                    <br>
                    <a href="/">Try Again</a>
                </body>
            </html>
        """.format(error.msg)


@app.get("/add_product/", response_class=HTMLResponse)
async def show_add_product_form(request: Request):
    return templates.TemplateResponse("addProductTemplate.html", {"request": request})


@app.post("/add_product/", response_class=RedirectResponse)
async def add_product(product_id: int = Form(...), product_name: str = Form(...), release_date: str = Form(...),
                      product_price: int = Form(...), software_requirements: str = Form(...),
                      hardware_requirements: str = Form(...), product_version: str = Form(...),
                      product_description: str = Form(...)):
    try:
        release_date = datetime.datetime.strptime(release_date, '%Y-%m-%d').date()
        query = "INSERT INTO Product (ProductID, ProductName, ReleaseDate, ProductPrice, SoftwareRequirements, " \
                "HardwareRequirements, ProductVersion, ProductDesription) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (product_id, product_name, release_date, product_price, software_requirements, hardware_requirements,
                  product_version, product_description)
        cursor.execute(query, values)
        db.commit()
        return RedirectResponse("/view_products/", status_code=303)
    except mysql.connector.errors.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Duplicate entry")
    except Exception as e:
        error_message = "An error occurred: " + str(e)
        return templates.TemplateResponse("errorTemplate.html", {"error_message": error_message})


@app.get("/view_products/", response_class=HTMLResponse)
async def view_products(request: Request):
    query = "SELECT * FROM Product"
    cursor.execute(query)
    products = cursor.fetchall()
    return templates.TemplateResponse("viewProductsTemplate.html", {"request": request, "products": products})


@app.get("/delete_product/", response_class=HTMLResponse)
async def delete_product_form(request: Request):
    return templates.TemplateResponse("deleteProductTemplate.html", {"request": request})


@app.post("/delete_product/", response_class=RedirectResponse)
async def delete_product(product_id: int = Form(...)):
    query = "DELETE FROM Product WHERE ProductID = %s"
    values = (product_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return RedirectResponse("/view_products/", status_code=303)


# Route to display modify product form
@app.get("/modify_product/", response_class=HTMLResponse)
async def modify_product_form(request: Request):
    return templates.TemplateResponse("modifyProductTemplate.html", {"request": request})


# Route to modify data in the Product table
@app.post("/modify_product/", response_class=RedirectResponse)
async def modify_product(product_id: int = Form(...), product_name: str = Form(None), release_date: str = Form(None),
                         product_price: int = Form(None),
                         software_requirements: str = Form(None), hardware_requirements: str = Form(None),
                         product_version: str = Form(None), product_description: str = Form(None)):
    set_query = ""
    values = ()
    if product_name:
        set_query += "ProductName = %s, "
        values += (product_name,)
    if release_date:
        set_query += "ReleaseDate = %s, "
        values += (release_date,)
    if product_price:
        set_query += "ProductPrice = %s, "
        values += (product_price,)
    if software_requirements:
        set_query += "SoftwareRequirements = %s, "
        values += (software_requirements,)
    if hardware_requirements:
        set_query += "HardwareRequirements = %s, "
        values += (hardware_requirements,)
    if product_version:
        set_query += "ProductVersion = %s, "
        values += (product_version,)
    if product_description:
        set_query += "ProductDescription = %s, "
        values += (product_description,)
    if not set_query:
        raise HTTPException(status_code=400, detail="No fields to modify")
    set_query = set_query[:-2]
    query = f"UPDATE Product SET {set_query} WHERE ProductID = %s"
    values += (product_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return RedirectResponse("/view_products", status_code=303)


# Route to display add license record form
@app.get("/add_license_record/", response_class=HTMLResponse)
async def show_add_license_record_form(request: Request):
    return templates.TemplateResponse("addLicenseRecordTemplate.html", {"request": request})


# Route to add data to the LicenseRecord table
@app.post("/add_license_record/", response_class=RedirectResponse)
async def add_license_record(license_record_id: int = Form(...), license_agreement_id: int = Form(...),
                             usage_data: str = Form(...), compliance_status: str = Form(...)):
    try:
        query = "INSERT INTO LicenseRecord (LicenseRecordID, LicenseAgreementID, UsageData, ComplianceStatus) VALUES " \
                "(%s, %s, %s, %s)"
        values = (license_record_id, license_agreement_id, usage_data, compliance_status)
        cursor.execute(query, values)
        db.commit()
        return RedirectResponse("/view_license_records/", status_code=303)
    except mysql.connector.errors.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Duplicate entry or check the foreign keys")
    except Exception as e:
        error_message = "An error occurred: " + str(e)
        return templates.TemplateResponse("errorTemplate.html", {"error_message": error_message})
    return RedirectResponse("view_license_records/", status_code=303)


# Route to display all license records
@app.get("/view_license_records/", response_class=HTMLResponse)
async def view_license_records(request: Request):
    query = "SELECT * FROM LicenseRecord"
    cursor.execute(query)
    license_records = cursor.fetchall()
    return templates.TemplateResponse("viewLicenseRecordsTemplate.html", {"request": request,
                                                                          "license_records": license_records})


# Route to display delete license record form
@app.get("/delete_license_record/", response_class=HTMLResponse)
async def delete_license_record_form(request: Request):
    return templates.TemplateResponse("deleteLicenseRecordTemplate.html", {"request": request})


# Route to delete data from the LicenseRecord table
@app.post("/delete_license_record/", response_class=RedirectResponse)
async def delete_license_record(license_record_id: int = Form(...)):
    query = "DELETE FROM LicenseRecord WHERE LicenseRecordID = %s"
    values = (license_record_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="License record not found")
    return RedirectResponse("/view_license_records/", status_code=303)


# Route to display modify license record form
@app.get("/modify_license_record/", response_class=HTMLResponse)
async def modify_license_record_form(request: Request):
    return templates.TemplateResponse("modifyLicenseRecordTemplate.html", {"request": request})


@app.post("/modify_license_record/", response_class=RedirectResponse)
async def modify_license_record(license_record_id: int = Form(...), license_agreement_id: int = Form(None),
                                usage_data: str = Form(None), compliance_status: str = Form(None)):
    set_query = ""
    values = ()
    if license_agreement_id:
        set_query += "LicenseAgreementID = %s, "
        values += (license_agreement_id,)
    if usage_data:
        set_query += "UsageData = %s, "
        values += (usage_data,)
    if compliance_status:
        set_query += "ComplianceStatus = %s, "
        values += (compliance_status,)
    if not set_query:
        raise HTTPException(status_code=400, detail="No fields to modify")
    set_query = set_query[:-2]
    query = f"UPDATE LicenseRecord SET {set_query} WHERE LicenseRecordID = %s"
    values += (license_record_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="License record not found")
    return RedirectResponse("/view_license_records", status_code=303)


@app.get("/add_license_agreement/", response_class=HTMLResponse)
async def show_add_license_agreement_form(request: Request):
    query = "SELECT * FROM Product"
    cursor.execute(query)
    products = cursor.fetchall()
    return templates.TemplateResponse("addLicenseAgreementTemplate.html", {"request": request, "products": products})


@app.post("/add_license_agreement/", response_class=RedirectResponse)
async def add_license_agreement(license_agreement_id: int = Form(...), product_id: int = Form(...),
                                license_agreement: str = Form(...)):
    query = "INSERT INTO LicenseAgreement (LicenseAgreementID, ProductID, LicenseAgreementcol) VALUES (%s, %s, %s)"
    values = (license_agreement_id, product_id, license_agreement)
    try:
        cursor.execute(query, values)
        db.commit()
        return RedirectResponse("/view_license_agreements/", status_code=303)
    except mysql.connector.errors.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Duplicate entry")
    except Exception as e:
        error_message = "An error occurred: " + str(e)
        return templates.TemplateResponse("errorTemplate.html", {"error_message": error_message})


@app.get("/view_license_agreements/", response_class=HTMLResponse)
async def view_license_agreements(request: Request):
    query = "SELECT la.LicenseAgreementID, p.ProductID, la.LicenseAgreementcol FROM LicenseAgreement la " \
            "JOIN Product p ON la.ProductID = p.ProductID"
    cursor.execute(query)
    license_agreements = cursor.fetchall()
    return templates.TemplateResponse("viewLicenseAgreementsTemplate.html",
                                      {"request": request, "license_agreements": license_agreements})


@app.get("/delete_license_agreement/", response_class=HTMLResponse)
async def delete_license_agreement_form(request: Request):
    return templates.TemplateResponse("deleteLicenseAgreementTemplate.html", {"request": request})


@app.post("/delete_license_agreement/", response_class=RedirectResponse)
async def delete_license_agreement(license_agreement_id: int = Form(...)):
    query = "DELETE FROM LicenseAgreement WHERE LicenseAgreementID = %s"
    values = (license_agreement_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="License agreement not found")
    return RedirectResponse("/view_license_agreements/", status_code=303)


# Route to display modify license agreement form
@app.get("/modify_license_agreement/", response_class=HTMLResponse)
async def modify_license_agreement_form(request: Request):
    # retrieve list of products to populate dropdown
    return templates.TemplateResponse("modifyLicenseAgreementTemplate.html", {"request": request})


# Route to modify data in the LicenseAgreement table
@app.post("/modify_license_agreement/", response_class=RedirectResponse)
async def modify_license_agreement(
        license_agreement_id: int = Form(...),
        product_id: int = Form(None),
        license_text: str = Form(None),
):
    set_query = ""
    values = ()
    if product_id is not None:
        set_query += "ProductID = %s, "
        values += (product_id,)
    if license_text is not None:
        set_query += "LicenseAgreementcol = %s, "
        values += (license_text,)
    if not set_query:
        raise HTTPException(status_code=400, detail="No fields to modify")
    set_query = set_query[:-2]
    query = f"UPDATE LicenseAgreement SET {set_query} WHERE LicenseAgreementID = %s"
    values += (license_agreement_id,)
    cursor.execute(query, values)
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="License agreement not found")
    return RedirectResponse("/view_license_agreements/", status_code=303)
