/*
 * Retrieve geospatial reference information from a GeoPDF document
 *
 * This pCOS sample searches for several different kinds of geospatial
 * information: three Flavors according to Adobe PDF 1.7 extension level 3
 * (these are equivalent to ISO 32000-2), and the proprietary TerraGo format:
 * 
 * (1) Page-based ISO viewports
 *
 * This flavor can be created with Acrobat by manually adding geospatial
 * reference information to a page. In PDFlib it can be created with the
 * "viewports" option of PDF_begin/end_page_ext().
 * 
 * (2) Image-based ISO viewports
 *
 * This flavor can be created with Acrobat by converting raster images (e.g.
 * GeoTIFF) to PDF. In PDFlib it can be created with the "georeference" option
 * of PDF_load_image().
 * 
 * (3) XObject-based ISO viewports
 *
 * This flavor is specified in ISO as well, but unfortunately it doesn't work in
 * Acrobat DC. It could be created with PDFlib, but this feature is disabled
 * since the resulting GeoPDF documents wouldn't work in Acrobat.
 * 
 * (4) Page-based geospatial information created by TerraGo.
 *
 * This flavor is created by the TerraGo software and is accepted by Acrobat
 * in addition to the ISO flavors.
 *
 * Required software: pCOS interface 8 (PDFlib+PDI/PPS 9, TET 4.1, PLOP 5.0)
 * Required data: PDF document with geospatical information
 */
package com.pdflib.cookbook.pcos.interactive;

import com.pdflib.IpCOS;
import com.pdflib.cookbook.pcos.pcos_cookbook_example;

public class geospatial extends pcos_cookbook_example {

    /* This is where the data files are. Adjust as necessary. */
    private final static String SEARCH_PATH = "../input";

    public void example_code(IpCOS p, int doc) throws 
        Exception {

        String path;
        String basepath;
        String objtype;

        System.out.println("File name: " + p.pcos_get_string(doc, "filename"));

        int pagecount = (int) p.pcos_get_number(doc, "length:pages");

        for (int page = 0; page < pagecount; page++) {
            System.out.println("page " + (page + 1) + ": ");

            /*
             * ************************************************************
             * (1) Page-based ISO viewports
             * ************************************************************
             */

            /* Iterate over all viewports which may be present on the page */
            basepath = "pages[" + page + "]/VP";
            int vpcount = (int) p.pcos_get_number(doc, "length:" + basepath);

            for (int v = 0; v < vpcount; v++) {
                System.out.println("  ISO viewport " + v + " on page:");
                dump_iso_viewport(p, basepath + "[" + v + "]", doc);
            }

            /*
             * ************************************************************
             * (2) Image-based ISO viewports
             * ************************************************************
             */

            /* Iterate over all images on the page */
            basepath = "pages[" + page + "]/images";
            int imagecount = (int) p.pcos_get_number(doc, "length:" + basepath);

            for (int image = 0; image < imagecount; image++) {
                path = basepath + "[" + image + "]/Measure/Subtype";
                objtype = p.pcos_get_string(doc, "type:" + path);

                if (objtype.equals("name")) {
                    String subtype = p.pcos_get_string(doc, path);

                    if (subtype.equals("GEO")) {
                        System.out.println("  ISO viewport on image " + image
                            + ": ");
                        basepath = "pages[" + page + "]/images[" + image + "]";
                        dump_iso_viewport(p, basepath, doc);
                    }
                }
            }

            /*
             * ************************************************************
             * (3) XObject-based ISO viewports
             * ************************************************************
             */
            /* Iterate over all Form XObjects on the page */
            basepath = "pages[" + page + "]/Resources/XObject";
            int xobjcount = (int) p.pcos_get_number(doc, "length:" + basepath);

            for (int xobj = 0; xobj < xobjcount; xobj++) {
                String subtype = p.pcos_get_string(doc, basepath + "[" + xobj
                    + "]/Subtype");

                /* Consider Form XObjects only (as opposed to Image XObjects */
                if (subtype.equals("Form")) {
                    path = basepath + "[" + xobj + "]/Measure/Subtype";
                    objtype = p.pcos_get_string(doc, "type:" + path);

                    if (objtype.equals("name")) {
                        subtype = p.pcos_get_string(doc, path);

                        if (subtype.equals("GEO")) {
                            System.out.println("  viewport on Form XObject "
                                + xobj + ": ");
                            basepath = "pages[" + page + "]/images[" + xobj
                                + "]";
                            dump_iso_viewport(p, basepath, doc);
                        }
                    }
                }
            }

            /*
             * ************************************************************
             * (4) Page-based TerraGo viewports
             * ************************************************************
             */

            /*
             * Iterate over all TerraGo viewports which may be present on the
             * page
             */
            path = "pages[" + page + "]/LGIDict";
            int tgcount = (int) p.pcos_get_number(doc, "length:" + path);

            for (int tg = 0; tg < tgcount; tg++) {
                System.out.println("  TerraGo viewport " + tg + ": ");
                basepath = path + "[" + tg + "]";
                dump_terrago_viewport(p, basepath, doc);
            }
        }
    }

    /* Emit some ISO viewport properties; can easily be extended */
    private void dump_iso_viewport(IpCOS p, String basepath, int doc)
        throws Exception {
        String path;
        String objtype;

        path = basepath + "/Measure/GCS/WKT";
        objtype = p.pcos_get_string(doc, "type:" + path);
        if (objtype.equals("string")) {
            System.out
                .println("    WKT='" + p.pcos_get_string(doc, path) + "'");
        }

        path = basepath + "/Measure/GCS/EPSG";
        objtype = p.pcos_get_string(doc, "type:" + path);
        if (objtype.equals("number")) {
            System.out
                .println("    EPSG=" + (int) p.pcos_get_number(doc, path));
        }

        /* Print the world coordinates for two points */
        path = basepath + "/Measure/GCS/GPTS[0]";
        System.out.println("    lat,lon="
            + p.pcos_get_number(doc, basepath + "/Measure/GPTS[0]") + ","
            + p.pcos_get_number(doc, basepath + "/Measure/GPTS[1]") + " to "
            + p.pcos_get_number(doc, basepath + "/Measure/GPTS[4]") + ","
            + p.pcos_get_number(doc, basepath + "/Measure/GPTS[5]"));

    }

    /* Emit some TerraGo viewport properties; can easily be extended */
    private void dump_terrago_viewport(IpCOS p, String basepath, int doc)
        throws Exception {
        String path;
        String objtype;

        path = basepath + "/Description";
        objtype = p.pcos_get_string(doc, "type:" + path);

        if (objtype.equals("string")) {
            System.out.println("    description='"
                + p.pcos_get_string(doc, path) + "'");
        }

        path = basepath + "/Display/Datum";
        objtype = p.pcos_get_string(doc, "type:" + path);

        if (objtype.equals("string")) {
            System.out.println("    display datum='"
                + p.pcos_get_string(doc, path) + "'");
        }

        path = basepath + "/Projection/ProjectionType";
        objtype = p.pcos_get_string(doc, "type:" + path);

        if (objtype.equals("string")) {
            System.out.println("    projection type='"
                + p.pcos_get_string(doc, path) + "'");
        }
    }

    public geospatial(String[] argv, String readable_name, String search_path) {
        super(argv, readable_name, search_path);
    }

    public static void main(String argv[]) {
        geospatial example = new geospatial(argv, "Geospatial data",
            SEARCH_PATH);
        example.execute();
    }
}
