// 
// Drawing functions
//
// Created 2021-11-05, skwok
//

function drawPolylines(ctx, lines, color, lw) {
    with (ctx) {
        strokeStyle = color;

        lineWidth = lw;
        beginPath();
        var x0 = 0,
            y0 = 0;
        let len = lines.length;
        let i;
        for (i = 0; i < len; ++i) {
            var row = lines[i];
            var x = row[0];
            var y = row[1];
            var code = row[2];
            if (code == 0) {
                x0 = x;
                y0 = y;
                moveTo(x, y);
                continue;
            }
            if (code == 1 || code == 3) {
                lineTo(x, y);
                continue;
            }
            if (code == 2) {
                lineTo(x0, y0);
            }
        }
        stroke();
    }
}

function drawQuadrilateral(ctx, x1, y1, x2, y2, x3, y3, x4, y4) {
    with (ctx) {
        beginPath();
        moveTo(x1, y1);
        lineTo(x2, y2);
        lineTo(x3, y3);
        lineTo(x4, y4);
        lineTo(x1, y1);
        stroke()
    }
}

function drawCross(ctx, x, y, xhalf, yhalf) {
    with (ctx) {
        beginPath();
        moveTo(x - xhalf, y - yhalf);
        lineTo(x + xhalf, y + yhalf);
        moveTo(x - xhalf, y + yhalf);
        lineTo(x + xhalf, y - yhalf);
        stroke()
    }
}

function drawCrossBig(ctx, x, y, xhalf, yhalf) {
    with (ctx) {
        beginPath();
        moveTo(x - 2 * xhalf, y - 2 * yhalf);
        lineTo(x - xhalf, y - yhalf);
        moveTo(x + xhalf, y + yhalf);
        lineTo(x + 2 * xhalf, y + 2 * yhalf);

        moveTo(x + 2 * xhalf, y - 2 * yhalf);
        lineTo(x + xhalf, y - yhalf);
        moveTo(x - xhalf, y + yhalf);
        lineTo(x - 2 * xhalf, y + 2 * yhalf);
        stroke();
    }
}


function drawPlus(ctx, x, y, xhalf, yhalf) {
    with (ctx) {
        beginPath();
        moveTo(x - xhalf, y);
        lineTo(x + xhalf, y);
        moveTo(x, y + yhalf);
        lineTo(x, y - yhalf);
        stroke()
    }
}

function drawPlusBig(ctx, x, y, xhalf, yhalf) {
    with (ctx) {
        beginPath();
        moveTo(x - 2 * xhalf, y);
        lineTo(x - xhalf, y);
        moveTo(x + xhalf, y);
        lineTo(x + 2 * xhalf, y);

        moveTo(x, y - 2 * yhalf);
        lineTo(x, y - yhalf);
        moveTo(x, y + yhalf);
        lineTo(x, y + 2 * yhalf);
        stroke()
    }
}

function drawRect(ctx, x0, y0, x1, y1) {
    with (ctx) {
        beginPath();
        moveTo(x0, y0);
        lineTo(x0, y1);
        lineTo(x1, y1);
        lineTo(x1, y0);
        lineTo(x0, y0);
        stroke()
    }
}

function drawCircle(ctx, x, y, rad) {
    with (ctx) {
        beginPath();
        moveTo(x + rad, y);
        arc(x, y, rad, 0, 2 * Math.PI);
        stroke();
    }
}

function drawArrow(ctx, x0, y0, x1, y1, size) {
    var dx = x1 - x0;
    var dy = y1 - y0;

    var len = Math.sqrt(dx * dx + dy * dy);
    var dx0 = dx / len;
    var dy0 = dy / len;
    var pdx = -dy0;
    var pdy = dx0;

    var px0 = x1 - dx0 * size;
    var py0 = y1 - dy0 * size;
    var size2 = size / 2;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.lineTo(px0 + pdx * size2, py0 + pdy * size2);
    ctx.lineTo(px0 - pdx * size2, py0 - pdy * size2);
    ctx.lineTo(x1, y1);
    ctx.stroke();
}
