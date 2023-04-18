import EmailPasswordReact from "supertokens-auth-react/recipe/emailpassword";
import SessionReact from "supertokens-auth-react/recipe/session";
import { appInfo } from "./appInfo";
import Router from "next/router";

export let frontendConfig = () => {
    return {
        appInfo,
        // recipeList contains all the modules that you want to
        // use from SuperTokens. See the full list here: https://supertokens.com/docs/guides
        recipeList: [EmailPasswordReact.init(
            {
                signInAndUpFeature: {
                    signUpForm: {
                        formFields: [
                            {
                                id: "first_name",
                                label: "Your first name",
                                placeholder: "First name"
                            }, {
                                id: "last_name",
                                label: "Your last name",
                                placeholder: "Last name",
                            }
                        ],
                        termsOfServiceLink: "https://example.com/terms-of-service",
                        privacyPolicyLink: "https://example.com/privacy-policy"
                    }
                }
            }
        ), SessionReact.init()],
        // this is so that the SDK uses the next router for navigation
        windowHandler: (oI) => {
            return {
                ...oI,
                location: {
                    ...oI.location,
                    setHref: (href) => {
                        Router.push(href);
                    },
                },
            };
        },
    };
};

export const recipeDetails = {
    docsLink: "https://supertokens.com/docs/emailpassword/introduction",
};
