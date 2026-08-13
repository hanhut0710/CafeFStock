import React from "react";

function formatDate(dateString) {
    if (!dateString) return "-";

    const date = new Date(dateString);

    if (Number.isNaN(date.getTime())) {
        return dateString;
    }

    return date.toLocaleDateString("vi-VN");
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return "-";

    return Number(value).toLocaleString("vi-VN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

function formatVolume(value) {
    if (value === null || value === undefined) return "-";

    return Number(value).toLocaleString("vi-VN");
}

export default function StockTable({ history = [] }) {
    const rows = [...history].sort(
        (a, b) =>
            new Date(b.trading_date) - new Date(a.trading_date)
    );

    return (
        <div className="stock-table-card">
            <div className="stock-table-header">
                <div>
                    <h3>Lịch sử giao dịch</h3>
                    <span>{rows.length} phiên giao dịch</span>
                </div>
            </div>

            <div className="stock-table-wrapper">
                <table className="stock-table">
                    <thead>
                        <tr>
                            <th>Mã chứng khoán</th>
                            <th>Ngày</th>
                            <th>Mở cửa</th>
                            <th>Cao nhất</th>
                            <th>Thấp nhất</th>
                            <th>Đóng cửa</th>
                            <th>Khối lượng</th>
                        </tr>
                    </thead>

                    <tbody>
                        {rows.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="empty-table">
                                    Không có dữ liệu giao dịch.
                                </td>
                            </tr>
                        ) : (
                            rows.map((row) => (
                                <tr
                                    key={`${row.symbol}-${row.trading_date}`}
                                >
                                    <td>{row.symbol}</td>
                                    <td>{formatDate(row.trading_date)}</td>

                                    <td>
                                        {formatNumber(row.open_price)}
                                    </td>

                                    <td>
                                        {formatNumber(row.high_price)}
                                    </td>

                                    <td>
                                        {formatNumber(row.low_price)}
                                    </td>

                                    <td className="close-price">
                                        {formatNumber(row.close_price)}
                                    </td>

                                    <td>
                                        {formatVolume(row.volume)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}