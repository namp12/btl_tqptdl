// Power Query (M) script: Nạp và làm sạch Sample - Superstore.csv trong Power BI Desktop
// Cách dùng: Home -> Transform data -> Advanced Editor -> Dán đoạn mã này (sửa lại đường dẫn file nếu cần)

let
    Source = Csv.Document(
        File.Contents("D:\truc quan phan tich du lieu\Sample - Superstore.csv"),
        [Delimiter = ",", Columns = 21, Encoding = 1252, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // Sử dụng locale "en-US" để parse đúng định dạng MM/DD/YYYY và dấu chấm thập phân
    TypedColumns = Table.TransformColumnTypes(
        PromotedHeaders,
        {
            {"Row ID", Int64.Type},
            {"Order ID", type text},
            {"Order Date", type date},
            {"Ship Date", type date},
            {"Ship Mode", type text},
            {"Customer ID", type text},
            {"Customer Name", type text},
            {"Segment", type text},
            {"Country", type text},
            {"City", type text},
            {"State", type text},
            {"Postal Code", type text},
            {"Region", type text},
            {"Product ID", type text},
            {"Category", type text},
            {"Sub-Category", type text},
            {"Product Name", type text},
            {"Sales", type number},
            {"Quantity", Int64.Type},
            {"Discount", type number},
            {"Profit", type number}
        },
        "en-US"
    ),
    // Chuẩn hóa Postal Code đủ 5 ký tự
    PaddedPostal = Table.TransformColumns(
        TypedColumns,
        {{"Postal Code", each Text.PadStart(Text.Trim(_), 5, "0"), type text}}
    ),
    // Loại bỏ bản ghi trùng lặp nghiệp vụ (bỏ qua Row ID)
    BusinessCols = List.RemoveItems(Table.ColumnNames(PaddedPostal), {"Row ID"}),
    Deduplicated = Table.Distinct(PaddedPostal, BusinessCols),
    // Tạo các cột dẫn xuất phục vụ phân tích thời gian và giao hàng
    AddedShippingDays = Table.AddColumn(
        Deduplicated,
        "Shipping Days",
        each Duration.Days([Ship Date] - [Order Date]),
        Int64.Type
    ),
    AddedOrderYear = Table.AddColumn(AddedShippingDays, "Order Year", each Date.Year([Order Date]), Int64.Type),
    AddedOrderMonth = Table.AddColumn(AddedOrderYear, "Order Month", each Date.Month([Order Date]), Int64.Type),
    AddedOrderQuarter = Table.AddColumn(
        AddedOrderMonth,
        "Order Quarter",
        each "Q" & Text.From(Date.QuarterOfYear([Order Date])),
        type text
    )
in
    AddedOrderQuarter
